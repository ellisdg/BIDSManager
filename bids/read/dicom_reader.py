import os
import glob
import subprocess
import shutil
import random

import dicom
from dicom.errors import InvalidDicomError

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.image import Image, DiffusionImage
from ..base.base import BIDSObject
from ..base.session import Session
from ..base.group import Group


def read_dicom_directory(input_directory, anonymize=False, length=2):
    dicom_files = get_dicom_files(input_directory)
    return dicoms_to_dataset(dicom_files, anonymize=anonymize, length=length)


def random_hash():
    number = random.getrandbits(128)
    key = "{0:032x}".format(number)
    return key


def random_tmp_directory():
    directory = os.path.join("/tmp", random_hash())
    os.makedirs(directory)
    return directory


def dicoms_to_dataset(dicom_files, anonymize=False, length=2):
    dataset = DataSet()
    sorted_dicoms = sort_dicoms(dicom_files, field="PatientName")
    subject_count = 0
    for subject_name in sorted_dicoms:
        session_count = 0
        if anonymize:
            subject_count += 1
            subject = Subject("{0:0{1}d}".format(subject_count, length))
        else:
            subject = Subject(subject_name)
        subject_dicoms = sort_dicoms(sorted_dicoms[subject_name], field="StudyDate")
        for date in subject_dicoms:
            if anonymize:
                session_count += 1
                session = Session("{0:0{1}d}".format(session_count, length))
            else:
                session = Session(date)
            image = subject_dicoms[date][0].get_image()
            if image.get_modality() in ["FLAIR"]:
                group = Group(name="anat")
            elif image.get_modality() in ["dwi"]:
                group = Group(name="dwi")
            else:
                print(image.get_modality())
                print(image.get_path())
            session.add_group(group)
            subject.add_session(session)
            group.add_image(image)
        dataset.add_subject(subject)
    return dataset


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
    return DicomFile(in_file).get_image()


def convert_dicom(dicom_file):
    file_path = dicom_file.get_path()
    if dicom_file.get_modality() == "dwi":
        return convert_dwi_dicom(file_path)
    else:
        nifti_file, sidecar_file = dcm2niix(file_path)
        return Image(path=nifti_file, modality=dicom_file.get_modality(), sidecar_path=sidecar_file,
                     acquisition=dicom_file.get_acquisition())


def convert_dwi_dicom(in_file):
    nifti_file, bval_file, bvec_file, sidecar_file = dcm2niix_dwi(in_file)
    return DiffusionImage(path=nifti_file, bval_path=bval_file, bvec_path=bvec_file, sidecar_path=sidecar_file)


def dcm2niix_dwi(in_file):
    working_dir = setup_dcm2niix(in_file)
    return run_dcm2niix(working_dir, working_dir, dwi=True)


def setup_dcm2niix(in_file):
    working_dir = random_tmp_directory()
    dicom_set = get_dicom_set(in_file)
    for dicom_file in dicom_set:
        shutil.copy(dicom_file.get_path(), working_dir)
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


def get_dicom_set(in_file):
    dicom_file = DicomFile(in_file)
    dicom_directory = os.path.dirname(in_file)
    dicom_files = get_dicom_files(dicom_directory)
    subject_dicoms = sort_dicoms(dicom_files, "PatientName")[dicom_file.get_field("PatientName")]
    session_dicoms = sort_dicoms(subject_dicoms, "StudyDate")[dicom_file.get_field("StudyDate")]
    series_dicoms = sort_dicoms(session_dicoms, "SeriesTime")[dicom_file.get_field("SeriesTime")]
    return series_dicoms


def run_dcm2niix(in_file, out_dir="/tmp/dcm2niix", dwi=False):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    subprocess.call(['dcm2niix', "-b", "y", "-o", out_dir, in_file])
    sidecar = glob.glob(os.path.join(out_dir, "*.json"))[0]
    if dwi:
        bval_file = glob.glob(os.path.join(out_dir, "*.bval"))[0]
        bvec_file = glob.glob(os.path.join(out_dir, "*.bvec"))[0]
        nifti_file = glob.glob(os.path.join(out_dir, "*.nii.gz"))[0]
        return nifti_file, bval_file, bvec_file, sidecar
    return glob.glob(os.path.join(out_dir, "*.nii.gz"))[0], sidecar


class DicomFile(BIDSObject):
    def __init__(self, *inputs, **kwargs):
        super(DicomFile, self).__init__(*inputs, **kwargs)
        self._info = None
        self.update()

    def update(self):
        if self._path:
            self._info = dicom.read_file(self._path)

    def get_modality(self):
        if "FLAIR" in self.get_series_description():
            return "FLAIR"
        elif "T2" in self.get_series_description():
            return "T2"
        elif "T1" in self.get_series_description():
            return "T1"
        elif "DTI" in self.get_series_description():
            return "dwi"

    def get_acquisition(self):
        if "GAD" in self.get_series_description():
            return "contrast"

    def get_series_description(self):
        if "SeriesDescription" in self._info:
            return self._info.SeriesDescription

    def get_image(self):
        return convert_dicom(self)

    def get_field(self, key):
        return self._info.get(key)
