import os
import glob
from subprocess import Popen, PIPE
import random
from warnings import warn
import datetime

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.session import Session
from ..utils.image_utils import load_image


def parse_image_keys(in_file, description, heuristic, case_sensitive=False):
    """
    Parse the image description (and in the future other image information) to
    determine the bids keys based on a heuristic provided by the user.
    :param in_file: nifti file output from dcm2niix
    :param description: Series Description provided in the filename from dcm2niix
    :param heuristic: user provided heuristic to get the keys from the image information
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive.
    :return: image_keys in dictionary format (will be None if image should be skipped)
    """
    image_keys = dict()
    if not case_sensitive:
        description = description.lower()
    for test_heuristic, test_keys in heuristic["SeriesDescription"]:
        if not case_sensitive:
            test_heuristic = test_heuristic.lower()
        if test_heuristic in description:
            if test_keys is None:
                print("{} found in {}. Skipping: {}".format(test_heuristic,
                                                            description,
                                                            in_file))
                return None
            image_keys.update(test_keys)

    if "modality" not in image_keys:
        # each valid image must have a modality
        warn(RuntimeWarning("No modality found for converted image: {}".format(in_file)))
        return None
    return image_keys


def manipulate_path_extension(in_file, in_ext, out_ext):
    return in_file.replace(in_ext, out_ext)


def get_secondary_output(primary_file, primary_ext, secondary_ext):
    secondary_file = manipulate_path_extension(primary_file, primary_ext, secondary_ext)
    if os.path.exists(secondary_file):
        return secondary_file


def parse_output(in_file, separator):
    return os.path.basename(in_file).split(separator)


def get_image(in_file, separator, heuristic, case_sensitive=False):
    """
    Get the image from the dcm2niix output file in BIDSManager format.
    :param in_file:
    :param separator:
    :param heuristic:
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive.
    :return:
    """
    subject_name, time, description, protocol, run = parse_output(in_file, separator)
    image_keys = parse_image_keys(in_file, description, heuristic=heuristic, case_sensitive=case_sensitive)
    # returns None if no image modality is found or image is to be skipped
    if image_keys:
        bval_path = get_secondary_output(in_file, ".nii.gz", ".bval")
        bvec_path = get_secondary_output(in_file, ".nii.gz", ".bvec")
        sidecar_path = get_secondary_output(in_file, ".nii.gz", ".json")
        return load_image(path_to_image=in_file, bval_path=bval_path, bvec_path=bvec_path,
                          path_to_sidecar=sidecar_path, **image_keys)


def convert_dicom_directory(input_directory,
                            heuristic,
                            anonymize=True,
                            separator="---",
                            bids_directory=None,
                            delete_intermediates=True,
                            verbose=False,
                            use_session_dates=False,
                            case_sensitive=False):
    """
    Convert a directory of DICOM files to BIDS format using dcm2niix.
    :param input_directory:
    :param heuristic:
    :param anonymize:
    :param separator:
    :param bids_directory:
    :param delete_intermediates:
    :param verbose:
    :param use_session_dates: If True, use the acquisition date to create session names.
    Default behavior is to put all the images in a single session. (default: False)
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive. (default: False)
    :return:
    """
    # TODO: add option to specify a subject name to subject ID mapping
    output_directory = random_tmp_directory()
    run_dcm2niix_on_directory(input_directory, output_directory, filename="%n{0}%t{0}%d{0}%p{0}".format(separator),
                              anonymize=anonymize, verbose=verbose)
    output_niftis = sorted(glob.glob(os.path.join(output_directory, "*.nii.gz")))
    dataset = DataSet()
    for f in output_niftis:
        subject_name, time, description, protocol, run = parse_output(f, separator)
        # what subject
        if dataset.has_subject_id(subject_name):
            subject = dataset.get_subject(subject_name)
        else:
            subject = Subject(subject_name)
            dataset.add_subject(subject)

        # parse acquisition date if use_session_dates is True
        if use_session_dates:
            # the variable time is expected to be in the format YYYYMMDDHHMMSS
            try:
                acquisition_date = datetime.datetime.strptime(time, "%Y%m%d%H%M%S")
                session_name = acquisition_date.strftime("%Y%m%d")
            except ValueError:
                warn(RuntimeWarning("Invalid time format: {}. Using empty session name.".format(time)))
                session_name = ""
        else:
            session_name = ""
        # TODO: keep track of date/times and sort sessions
        #       by dates, then anonymize them into session numbers.

        # what session
        if subject.has_session(session_name):
            session = subject.get_session(session_name)
        else:
            session = Session(session_name)
            subject.add_session(session)

        # add image
        image = get_image(f, separator, heuristic=heuristic, case_sensitive=case_sensitive)
        # TODO: Add SBRef images to a certain group
        if image:
            session.add_image(image)

        # TODO: add intendedfor metadata for epi images
        #       this could simply be looking for the nearest bold or dwi image
        #       and saying that the epi image was intended for that image

    # TODO: squeeze sessions

    if bids_directory:
        print("Writing bids directory: {}".format(bids_directory))
        dataset.set_path(bids_directory)
        if delete_intermediates:
            dataset.update(move=True)
        else:
            dataset.update(move=False)

    return dataset


def random_hash():
    number = random.getrandbits(128)
    key = "{0:032x}".format(number)
    return key


def random_tmp_directory():
    directory = os.path.join("/tmp", "bidsmanager_" + random_hash())
    os.makedirs(directory)
    return directory


def run_dcm2niix_on_directory(input_directory, output_directory, filename="%t%d%n%p", anonymize=True,
                              verbose=False, directory_depth=9):
    command = ['dcm2niix', "-b", "y", "-ba", "-z", "y", "-d", str(directory_depth),
               "-o", output_directory, "-f", filename, input_directory]
    if anonymize:
        command.insert(4, "y")
    else:
        command.insert(4, "n")
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = process.communicate()
    if verbose:
        print("dcm2niix output: {}".format(output.decode()))
        print("dcm2niix error: {}".format(err.decode()))
    parse_cmd_output(output)


def parse_cmd_output(cmd_output):
    if "No valid DICOM files were found" in str(cmd_output):
        raise RuntimeError("No valid DICOM files were found")

