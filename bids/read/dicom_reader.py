import os
import glob
import subprocess
import shutil
import random

import dicom
from dicom.errors import InvalidDicomError

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.image import Image
from ..base.base import BIDSObject
from ..base.session import Session
from ..base.group import Group


def read_dicom_directory(input_directory):
    dicom_files = get_dicom_files(input_directory)
    return dicoms_to_dataset(dicom_files)


def random_hash():
    number = random.getrandbits(128)
    key = "{0:032x}".format(number)
    return key


def random_tmp_directory():
    directory = os.path.join("/tmp", random_hash())
    os.makedirs(directory)
    return directory


def dicoms_to_dataset(dicom_files):
    dataset = DataSet()
    sorted_dicoms = sort_dicoms(dicom_files, field="PatientName")
    for subject_name in sorted_dicoms:
        subject = Subject(subject_name)
        subject_dicoms = sort_dicoms(sorted_dicoms[subject_name], field="StudyDate")
        for date in subject_dicoms:
            session = Session(date)
            session.add_group(Group(images=[subject_dicoms[date][0].get_image()]))
            subject.add_session(session)
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
    return Image(path=dcm2niix(dicom_file.get_path()), modality=dicom_file.get_modality(),
                 acquisition=dicom_file.get_acquisition())


def dcm2niix(in_file):
    working_dir = random_tmp_directory()
    dicom_set = get_dicom_set(in_file)
    for dicom_file in dicom_set:
        shutil.copy(dicom_file.get_path(), working_dir)
    base_path, _ = os.path.splitext(in_file)
    out_file = base_path + ".nii.gz"
    tmp_file = run_dcm2niix(working_dir, working_dir)
    return tmp_file


def get_dicom_set(in_file):
    dicom_file = DicomFile(in_file)
    dicom_directory = os.path.dirname(in_file)
    dicom_files = get_dicom_files(dicom_directory)
    subject_dicoms = sort_dicoms(dicom_files, "PatientName")[dicom_file.get_field("PatientName")]
    session_dicoms = sort_dicoms(subject_dicoms, "StudyDate")[dicom_file.get_field("StudyDate")]
    series_dicoms = sort_dicoms(session_dicoms, "SeriesTime")[dicom_file.get_field("SeriesTime")]
    return series_dicoms


def run_dcm2niix(in_file, out_dir="/tmp/dcm2niix"):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    subprocess.call(['dcm2niix', "-o", out_dir, in_file])
    tmp_file = glob.glob(os.path.join(out_dir, "*.nii.gz"))[0]
    return tmp_file


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
