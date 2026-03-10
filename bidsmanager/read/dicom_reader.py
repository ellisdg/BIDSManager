import os
import glob
from subprocess import Popen, PIPE
import random
from warnings import warn
import datetime
import csv

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.session import Session
from ..utils.image_utils import load_image
from ..utils.session_utils import modality_to_group_name


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


def _normalize_mapping_value(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith(".0"):
        try:
            return str(int(float(text)))
        except ValueError:
            return text
    return text


def _read_mapping_rows(subject_map=None):
    rows = []
    if not subject_map:
        return rows
    if not os.path.exists(subject_map):
        warn(RuntimeWarning("Subject mapping file not found: {}".format(subject_map)))
        return rows

    extension = os.path.splitext(subject_map)[-1].lower()
    if extension == ".csv":
        with open(subject_map, "r") as f:
            reader = csv.DictReader(f)
            rows.extend(list(reader))
        return rows

    if extension in (".xls", ".xlsx"):
        try:
            import pandas as pd
            frame = pd.read_excel(subject_map)
            rows.extend(frame.to_dict(orient="records"))
        except Exception as exc:
            warn(RuntimeWarning("Could not read subject mapping excel file {}: {}".format(subject_map, exc)))
            # Fallback for lightweight test environments: treat file as CSV-like text.
            try:
                with open(subject_map, "r") as f:
                    reader = csv.DictReader(f)
                    rows.extend(list(reader))
            except Exception:
                pass
        return rows

    warn(RuntimeWarning("Unsupported subject mapping extension for {}. Expected .csv/.xls/.xlsx".format(subject_map)))
    return rows


def _build_subject_session_mapping(subject_map=None):
    subject_map_dict = {}
    session_map_dict = {}
    rows = _read_mapping_rows(subject_map=subject_map)
    for row in rows:
        source_subject = _normalize_mapping_value(row.get("source_subject") or row.get("source") or row.get("subject"))
        bids_subject = _normalize_mapping_value(row.get("bids_subject") or row.get("subject_id") or row.get("bids_id"))
        session_id = _normalize_mapping_value(row.get("session_id") or row.get("session") or row.get("ses"))
        if not source_subject:
            continue
        if bids_subject:
            subject_map_dict[source_subject] = bids_subject
        if session_id:
            session_map_dict[source_subject] = session_id
    return subject_map_dict, session_map_dict


def _session_from_time(time_value):
    try:
        acquisition_date = datetime.datetime.strptime(time_value, "%Y%m%d%H%M%S")
        return acquisition_date.strftime("%Y%m%d")
    except ValueError:
        warn(RuntimeWarning("Invalid time format: {}. Using empty session name.".format(time_value)))
        return ""


def _path_exists_for_image(image, subject_name, session_name, bids_directory):
    if not bids_directory:
        return False
    group_name = modality_to_group_name(image.get_modality())
    parts = [bids_directory, "sub-{}".format(subject_name)]
    if session_name:
        parts.append("ses-{}".format(session_name))
    parts.append(group_name)

    # Image is not attached to a Session yet, so build the final BIDS basename explicitly.
    basename_parts = ["sub-{}".format(subject_name)]
    if session_name:
        basename_parts.append("ses-{}".format(session_name))
    basename_parts.append(image.get_image_key())
    out_file = os.path.join(*parts, "_".join(basename_parts) + image.get_extension())
    return os.path.exists(out_file)


def _increment_run_until_unique(image, session, subject_name, session_name, bids_directory):
    # Keep incrementing run until neither the in-memory session nor the output filesystem has a conflict.
    run_number = image.get_run_number() if image.get_run_number() else 1
    image.set_run_number(run_number)
    while session.get_images(modality=image.get_modality(), task=image.get_task_name(),
                             acq=image.get_acquisition(), ce=image.get_contrast(), dir=image.get_direction(),
                             rec=image.get_reconstruction(), run=image.get_run_number()) or \
            _path_exists_for_image(image, subject_name, session_name, bids_directory):
        run_number += 1
        image.set_run_number(run_number)


def convert_dicom_directory(input_directory,
                            heuristic,
                            anonymize=True,
                            separator="---",
                            bids_directory=None,
                            delete_intermediates=True,
                            verbose=False,
                            use_session_dates=False,
                            combine_sessions=False,
                            subject_map=None,
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
    :param combine_sessions: If True, put all images for a subject in a single no-session directory.
    :param subject_map: CSV/XLS/XLSX mapping file for source_subject -> bids_subject/session.
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive. (default: False)
    :return:
    """
    output_directory = random_tmp_directory()
    run_dcm2niix_on_directory(input_directory, output_directory, filename="%n{0}%t{0}%d{0}%p{0}".format(separator),
                              anonymize=anonymize, verbose=verbose)
    output_niftis = sorted(glob.glob(os.path.join(output_directory, "*.nii.gz")))
    dataset = DataSet()

    # Heuristic-level mapping paths are supported for backwards compatibility.
    if subject_map is None:
        subject_map = heuristic.get("subject_map")
    # Backward compatibility for older heuristic keys.
    if subject_map is None:
        subject_map = heuristic.get("subject_map_csv") or heuristic.get("subject_map_excel")

    subject_name_map, session_name_map = _build_subject_session_mapping(subject_map=subject_map)

    for f in output_niftis:
        source_subject_name, time, description, protocol, run = parse_output(f, separator)
        _ = (description, protocol, run)

        # Apply optional source->BIDS subject mapping.
        subject_name = subject_name_map.get(source_subject_name, source_subject_name)

        if dataset.has_subject_id(subject_name):
            subject = dataset.get_subject(subject_name)
        else:
            subject = Subject(subject_name)
            dataset.add_subject(subject)

        # session mapping precedence: explicit mapping > date-derived > combined/no-session
        if combine_sessions:
            session_name = ""
        elif source_subject_name in session_name_map:
            session_name = session_name_map[source_subject_name]
        elif use_session_dates:
            session_name = _session_from_time(time)
        else:
            session_name = ""

        if subject.has_session(session_name):
            session = subject.get_session(session_name)
        else:
            session = Session(session_name)
            subject.add_session(session)

        image = get_image(f, separator, heuristic=heuristic, case_sensitive=case_sensitive)
        if image:
            # Ensure new conversions do not overwrite files in an existing destination session.
            _increment_run_until_unique(image=image,
                                        session=session,
                                        subject_name=subject_name,
                                        session_name=session_name,
                                        bids_directory=bids_directory)
            session.add_image(image)

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
