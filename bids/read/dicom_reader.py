import os
import glob

import dicom

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.image import Image
from ..base.base import BIDSObject


def read_dicom_directory(input_directory):
    dicom_files = get_dicom_files(input_directory)
    return DataSet([Subject(name) for name in group_dicoms(dicom_files)])


def group_dicoms(dicom_files):
    keys = set()
    for dicom_file in dicom_files:
        key = dicom_file.get_field("PatientName")
        keys.add(key)
    return keys


def get_dicom_files(input_directory):
    dicom_files = []
    for f in get_files_in_directory(input_directory):
        dicom_files.append(DicomFile(f))
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
        return Image(modality=self.get_modality(), acquisition=self.get_acquisition())

    def get_field(self, key):
        return self._info.get(key)
