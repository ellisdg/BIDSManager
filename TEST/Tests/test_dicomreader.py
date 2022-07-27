import glob
import gzip
import os
import tarfile
from unittest import TestCase
import unittest

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

import nibabel as nib

from bidsmanager.read.dicom_reader import read_dicom_file, read_dicom_directory


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
    @classmethod
    def _setUpClass(cls):
        super(TestDicomReader, cls).setUpClass()
        cls.dicom_files = dict()
        TestDicomReader.setUpDicomFiles(cls.dicom_files)
        TestDicomReader.setUpFlair(cls.dicom_files)

    @staticmethod
    def _setUpDicomFiles(dicom_files):
        dicom_dir = os.path.join("tmp", "DICOMDIR")
        if not os.path.exists(dicom_dir):
            file_url = "ftp://medical.nema.org/medical/dicom/Multiframe/MR/nemamfmr.imagesAB.tar.bz2"
            temp_file = download_file(file_url)
            extract_tarball_files(temp_file, dicom_dir)
        for f in glob.glob(os.path.join(dicom_dir, "DISCIMG", "IMAGES", "*")):
            dicom_files[os.path.basename(f).split(".")[0]] = f

    @staticmethod
    def setUpFlair(dicom_files):
        temp_dicom = os.path.join("tmp", "MR-MONO2-16-head.dcm")
        if not os.path.exists(temp_dicom):
            file_url = "http://www.barre.nom.fr/medical/samples/files/MR-MONO2-16-head.gz"
            temp_file = download_file(file_url)
            unzip_file(temp_file, temp_dicom)
        dicom_files["MR-MONO2-16-head"] = temp_dicom

    def _test_image_modality(self, image, modality):
        self.assertEqual(image.get_modality(), modality)

    def test_read_flair(self):
        raise unittest.SkipTest("Skipping dicom tests")
        # Don't run this test for now
        image_file = read_dicom_file(self.dicom_files["MR-MONO2-16-head"]).get_path()
        test_image_file = os.path.join("TestNiftis", "MR-MONO2-16-head.nii.gz")
        self.assertEqual(nib.load(image_file).header, nib.load(test_image_file).header)

    def test_read_t1(self):
        raise unittest.SkipTest("Skipping dicom tests")
        image = read_dicom_file(self.dicom_files["BRTUM008"])
        self._test_image_modality(image, "T1w")
        self.assertEqual(image.get_contrast(), 'gad')

    def test_read_t2(self):
        raise unittest.SkipTest("Skipping dicom tests")
        image = read_dicom_file(self.dicom_files["BRTUM014"])
        self._test_image_modality(image, "T2w")
