import os
import glob
from subprocess import Popen, PIPE
import shutil
import random
from warnings import warn

import pydicom as dicom
from pydicom.errors import InvalidDicomError
import nibabel as nib

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.image import DiffusionImage
from ..base.base import BIDSObject
from ..base.session import Session
from ..utils.image_utils import load_image
from ..utils.dataset_utils import anonymize_dataset


def read_dicom_directory(input_directory, anonymize=False, id_length=2, skip_image_descriptions=(),
                         image_modality_heuristic=None):
    return convert_directory(input_directory, skip_image_descriptions=skip_image_descriptions, anonymize=anonymize,
                             image_modality_heuristic=image_modality_heuristic)


def get_acquisition(description):
    if is_contrast(description):
        return "contrast"


def get_image_modality(in_file, description, heuristic=None):
    modality = description_to_modality(description, heuristic=heuristic)
    if not modality and is_4d(in_file):
        return "bold"
    return modality


def is_4d(in_file):
    n_dims = len(nib.load(in_file).header.get_data_shape())
    return n_dims == 4


def is_contrast(description):
    return "gad" in description.lower() or "+c" in description.lower()


def manipulate_path_extension(in_file, in_ext, out_ext):
    return in_file.replace(in_ext, out_ext)


def get_secondary_output(primary_file, primary_ext, secondary_ext):
    secondary_file = manipulate_path_extension(primary_file, primary_ext, secondary_ext)
    if os.path.exists(secondary_file):
        return secondary_file


def parse_output(in_file, separator):
    return os.path.basename(in_file).split(separator)


def get_image(in_file, separator, skip_image_descriptions, image_modality_heuristic=None):
    subject_name, time, description, protocol, run = parse_output(in_file, separator)
    if not skip_series(description, skip_image_descriptions):
        modality = get_image_modality(in_file, description, heuristic=image_modality_heuristic)
        bval_path = get_secondary_output(in_file, ".nii.gz", ".bval")
        bvec_path = get_secondary_output(in_file, ".nii.gz", ".bvec")
        sidecar_path = get_secondary_output(in_file, ".nii.gz", ".json")
        task_name = "".join(description.lower().split("_"))
        acquisition = get_acquisition(description)
        return load_image(path_to_image=in_file, modality=modality, bval_path=bval_path, bvec_path=bvec_path,
                          path_to_sidecar=sidecar_path, acquisition=acquisition, task_name=task_name)


def convert_directory(input_directory, skip_image_descriptions=None, anonymize=False, image_modality_heuristic=None,
                      separator="---"):
    output_directory = random_tmp_directory()
    run_dcm2niix_on_directory(input_directory, output_directory, filename="%n{0}%t{0}%d{0}%p{0}".format(separator),
                              anonymize=anonymize)
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

        # what session
        if subject.has_session(time):
            session = subject.get_session(time)
        else:
            session = Session(time)
            subject.add_session(session)

        # add image
        image = get_image(f, separator, skip_image_descriptions, image_modality_heuristic=image_modality_heuristic)
        # todo: test for duplicates
        if image:
            session.add_image(image)

    if anonymize:
        return anonymize_dataset(dataset)
    return dataset


def random_hash():
    number = random.getrandbits(128)
    key = "{0:032x}".format(number)
    return key


def random_tmp_directory():
    directory = os.path.join("/tmp", "bidsmanager_" + random_hash())
    os.makedirs(directory)
    return directory


def dicoms_to_dataset(dicom_files, anonymize=False, id_length=2, skip_image_descriptions=None,
                      subject_field="PatientName", session_field="StudyDate", series_field="SeriesDescription",
                      series_time="SeriesTime"):
    dataset = DataSet()
    sorted_dicoms = sort_dicoms(dicom_files, field=subject_field)
    subject_count = 0
    for subject_name in sorted_dicoms:
        session_count = 0
        if anonymize:
            subject_count += 1
            subject = Subject("{0:0{1}d}".format(subject_count, id_length))
        else:
            subject = Subject(subject_name)
        dataset.add_subject(subject)
        subject_dicoms = sort_dicoms(sorted_dicoms[subject_name], field=session_field)
        for date in sorted(subject_dicoms.keys()):
            if anonymize:
                session_count += 1
                session = Session("{0:0{1}d}".format(session_count, id_length))
            else:
                session = Session(date)
            subject.add_session(session)
            session_dicoms = sort_dicoms(subject_dicoms[date], field=series_field)
            for description in session_dicoms:
                if not skip_series(description=description, skip_image_descriptions=skip_image_descriptions):
                    series_dicoms = sort_dicoms(session_dicoms[description], field=series_time)
                    for i, time in enumerate(sorted(series_dicoms.keys())):
                        try:
                            session.add_image(convert_dicoms(series_dicoms[time]))
                        except RuntimeError:
                            continue
    return dataset


def skip_series(description, skip_image_descriptions):
    for image_description in skip_image_descriptions:
        if not description or image_description in description:
            return True
    return False


def sort_dicoms(dicom_files, field="PatientName"):
    dicoms = dict()
    for dicom_file in dicom_files:
        key = dicom_file.get_field(field)
        if key not in dicoms:
            dicoms[key] = [dicom_file]
        else:
            dicoms[key].append(dicom_file)
    return dicoms


def get_dicom_files(input_directory):
    dicom_files = []
    for f in get_files_in_directory(input_directory):
        try:
            dicom_files.append(DicomFile(f))
        except InvalidDicomError:
            continue
    return dicom_files


def get_files_in_directory(input_directory):
    files = []
    for item in glob.glob(os.path.join(input_directory, "*")):
        if os.path.isdir(item):
            files.extend(get_files_in_directory(item))
        elif os.path.isfile(item):
            files.append(item)
    return files


def read_dicom_file(in_file):
    return convert_dicoms([DicomFile(in_file)])


def convert_dicom(dicom_file):
    file_path = dicom_file.get_path()
    modality = dicom_file.get_modality()
    task_name = dicom_file.get_series_description().lower().replace(" ", "")
    acquisition = dicom_file.get_acquisition()
    return convert_dicom_file_path(file_path=file_path, modality=modality, task_name=task_name, acquisition=acquisition)


def convert_dicom_file_path(file_path, modality, acquisition, task_name):
    if modality == "dwi":
        return convert_dwi_dicom(file_path)
    else:
        nifti_file, sidecar_file = dcm2niix(file_path)
        return load_image(path_to_image=nifti_file, modality=modality, path_to_sidecar=sidecar_file,
                          task_name=task_name, acquisition=acquisition)


def convert_dicoms(dicom_objects):
    file_paths = [dicom_object.get_path() for dicom_object in dicom_objects]
    modality = dicom_objects[0].get_modality()
    task_name = dicom_objects[0].get_series_description().lower().replace(" ", "")
    acquisition = dicom_objects[0].get_acquisition()
    return convert_dicom_file_path(file_path=file_paths, modality=modality, task_name=task_name,
                                   acquisition=acquisition)


def convert_dwi_dicom(in_file):
    nifti_file, bval_file, bvec_file, sidecar_file = dcm2niix_dwi(in_file)
    return DiffusionImage(path=nifti_file, bval_path=bval_file, bvec_path=bvec_file, sidecar_path=sidecar_file)


def dcm2niix_dwi(in_file):
    working_dir = setup_dcm2niix(in_file)
    return run_dcm2niix(working_dir, working_dir, dwi=True)


def setup_dcm2niix(in_file):
    working_dir = random_tmp_directory()
    if isinstance(in_file, list):
        dicom_files = in_file
    else:
        dicom_files = [dicom_file.get_path() for dicom_file in get_dicom_set(in_file)]
    for dicom_file in dicom_files:
        shutil.copy(dicom_file, working_dir)
    return working_dir


def dcm2niix(in_file, out_file=None):
    working_dir = setup_dcm2niix(in_file)
    tmp_file, tmp_sidecar = run_dcm2niix(working_dir, working_dir)

    if out_file:
        shutil.move(tmp_file, out_file)
        sidecar = out_file.replace(".nii.gz", ".json")
        shutil.move(tmp_sidecar, sidecar)
    else:
        out_file = tmp_file
        sidecar = tmp_sidecar
    return out_file, sidecar


def get_dicom_set(in_file, subject_field="PatientName", session_field="StudyDate", series_field="SeriesTime"):
    dicom_file = DicomFile(in_file)
    dicom_directory = os.path.dirname(in_file)
    dicom_files = get_dicom_files(dicom_directory)
    subject_dicoms = sort_dicoms(dicom_files, subject_field)[dicom_file.get_field(subject_field)]
    session_dicoms = sort_dicoms(subject_dicoms, session_field)[dicom_file.get_field(session_field)]
    series_dicoms = sort_dicoms(session_dicoms, series_field)[dicom_file.get_field(series_field)]
    return series_dicoms


def run_dcm2niix_on_directory(input_directory, output_directory, filename="%t%d%n%p", anonymize=False):
    command = ['dcm2niix', "-b", "y", "-ba", "-z", "y", "-o", output_directory, "-f", filename, input_directory]
    if anonymize:
        command.insert(4, "y")
    else:
        command.insert(4, "n")
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = process.communicate()
    parse_cmd_output(output)


def run_dcm2niix(in_file, out_dir="/tmp/dcm2niix", dwi=False):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    command = ['dcm2niix', "-b", "y", "-z", "y", "-o", out_dir, in_file]
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = process.communicate()
    parse_cmd_output(output)
    return get_dcm2niix_outputs(out_dir=out_dir, dwi=dwi)


def parse_cmd_output(cmd_output):
    if "No valid DICOM files were found" in str(cmd_output):
        raise RuntimeError("No valid DICOM files were found")


def get_dcm2niix_outputs(out_dir, dwi=False):
    sidecar_file = get_output_file(out_dir, ".json")
    if dwi:
        return get_dcm2niix_dwi_outputs(out_dir=out_dir, sidecar_file=sidecar_file)
    nifti_file = get_output_file(out_dir, ".nii.gz")
    return nifti_file, sidecar_file


def get_dcm2niix_dwi_outputs(out_dir, sidecar_file):
    nifti_files = glob.glob(os.path.join(out_dir, "*.nii.gz"))
    for nifti_file in nifti_files:
        if "ADC" not in nifti_file:
            break
    bval_file = get_output_file(out_dir, ".bval")
    bvec_file = get_output_file(out_dir, ".bvec")
    return nifti_file, bval_file, bvec_file, sidecar_file


def get_output_file(output_directory, extension):
    output_files = glob.glob(os.path.join(output_directory, "*" + extension))
    if len(output_files) > 1:
        warn("Multiple output files found:\n\t{0}".format("\n\t".join(output_files)), RuntimeWarning)
    return output_files[0]


default_heuristic = {"epi": ["SpinEchoFieldMap"],
                     "sbref": ["SBRef"],
                     "FLAIR": ["FLAIR"],
                     "T2w": ["T2"],
                     "T1w": ["T1"],
                     "dwi": ["DTI", "DWI", "dmri", "dMRI"],
                     "bold": ["bold", "fMRI"]}


def description_to_modality(description, heuristic=None):
    if heuristic is None:
        heuristic = default_heuristic
    for key, values in heuristic.items():
        for value in values:
            if value in description:
                return key
    warn(RuntimeWarning("No modality found for description: {}".format(description)))


class DicomFile(BIDSObject):
    def __init__(self, path, tags_to_save=("PatientName", "StudyDate", "SeriesTime", "SeriesDescription",
                                           "NumberOfTemporalPositions"), *inputs, **kwargs):
        super(DicomFile, self).__init__(path=path, *inputs, **kwargs)
        self._info = dict()
        self.save_tags(tags_to_save)

    def get_data(self):
        if self._path and os.path.exists(self._path):
            return dicom.read_file(self._path)

    def get_modality(self):
        modality = description_to_modality(self.get_series_description())
        if (modality is None and self.get_field("NumberOfTemporalPositions")
                and int(self.get_field("NumberOfTemporalPositions")) > 1):
            return "bold"
        else:
            return modality

    def get_acquisition(self):
        if "GAD" in self.get_series_description() or "+C" in self.get_series_description():
            return "contrast"

    def get_series_description(self):
        return self.get_field("SeriesDescription")

    def get_image(self):
        return convert_dicom(self)

    def get_field(self, key):
        try:
            return str(self._info[key])
        except KeyError:
            dicom_data = self.get_data()
            if key in dicom_data:
                return str(dicom_data.get(key))

    def save_tags(self, tags_to_save):
        dicom_data = self.get_data()
        for tag in tags_to_save:
            self._info[tag] = dicom_data.get(tag)
