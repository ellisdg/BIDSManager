from unittest import TestCase
import gzip
import tarfile
import os
import glob
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

from ..read.dicom_reader import read_dicom_file


def extract_tarball_files(in_file, output_dir):
    _, ext = os.path.splitext(in_file)
    opened_file = tarfile.open(in_file, "r:{0}".format(ext.lstrip(".")))
    opened_file.extractall(output_dir)


def download_gzipped_file(file_url, out_file):
    temp_file = download_file(file_url)
    unzip_file(temp_file, out_file)


def download_file(file_url):
    filename, headers = urlretrieve(file_url)
    return filename


def unzip_file(in_file, out_file):
    file_data = read_zipped_file(in_file)
    write_data_to_file(file_data, out_file)


def read_zipped_file(filename):
    with gzip.GzipFile(filename) as opened_file:
        file_data = opened_file.read()
    return file_data


def write_data_to_file(data, out_file):
    with open(out_file, "wb") as opened_file:
        opened_file.write(data)


class TestDicomReader(TestCase):
    def setUp(self):
        self.dicom_files = dict()
        self.setUpDicomFiles()
        self.setUpFlair()

    def setUpDicomFiles(self):
        dicom_dir = os.path.join("tmp", "DICOMDIR")
        if not os.path.exists(dicom_dir):
            file_url = "ftp://medical.nema.org/medical/dicom/Multiframe/MR/nemamfmr.imagesAB.tar.bz2"
            temp_file = download_file(file_url)
            extract_tarball_files(temp_file, dicom_dir)
        for f in glob.glob(os.path.join(dicom_dir, "DISCIMG", "IMAGES", "*")):
            self.dicom_files[os.path.basename(f).split(".")[0]] = f

    def setUpFlair(self):
        temp_dicom = os.path.join("tmp", "MR-MONO2-16-head" + ".dcm")
        if not os.path.exists(temp_dicom):
            file_url = "http://www.barre.nom.fr/medical/samples/files/MR-MONO2-16-head.gz"
            temp_file = download_file(file_url)
            unzip_file(temp_file, temp_dicom)
        self.dicom_files["MR-MONO2-16-head"] = temp_dicom

    def _test_image_modality(self, image, modality):
        self.assertEqual(image.get_modality(), modality)

    def test_read_flair(self):
        image = read_dicom_file(self.dicom_files["MR-MONO2-16-head"])
        self._test_image_modality(image, "FLAIR")

    def test_read_t1(self):
        image = read_dicom_file(self.dicom_files["BRTUM008"])
        self._test_image_modality(image, "T1")
