import dicom

from ..base.image import Image
from ..base.base import BIDSObject


def read_dicom_file(in_file):
    return DicomFile(in_file).get_image()


class DicomFile(BIDSObject):
    def __init__(self, *inputs, **kwargs):
        super(DicomFile, self).__init__(*inputs, **kwargs)
        if self._path:
            self._info = dicom.read_file(self._path)
        else:
            self._info = None

    def get_modality(self):
        if "FLAIR" in self.get_series_name():
            return "FLAIR"
        else:
            return "T1"

    def get_series_name(self):
        if "SeriesDescription" in self._info:
            return self._info.SeriesDescription

    def get_image(self):
        return Image(modality=self.get_modality())

