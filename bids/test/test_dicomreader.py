from unittest import TestCase
import gzip
import tarfile
import os
import glob
import shutil
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

import nibabel as nib

from ..read.dicom_reader import read_dicom_file, read_dicom_directory, dcm2niix
from ..write.dataset_writer import write_dataset


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
        temp_dicom = os.path.join("tmp", "MR-MONO2-16-head.dcm")
        if not os.path.exists(temp_dicom):
            file_url = "http://www.barre.nom.fr/medical/samples/files/MR-MONO2-16-head.gz"
            temp_file = download_file(file_url)
            unzip_file(temp_file, temp_dicom)
        self.dicom_files["MR-MONO2-16-head"] = temp_dicom

    def _test_image_modality(self, image, modality):
        self.assertEqual(image.get_modality(), modality)

    def test_read_flair(self):
        image_file = read_dicom_file(self.dicom_files["MR-MONO2-16-head"]).get_path()
        test_image_file = os.path.join("..", "..", "TEST", "TestNiftis", "MR-MONO2-16-head.nii.gz")
        self.assertEqual(nib.load(image_file).header, nib.load(test_image_file).header)

    def test_read_t1(self):
        image = read_dicom_file(self.dicom_files["BRTUM008"])
        self._test_image_modality(image, "T1")
        self.assertEqual(image.get_acquisition(), 'contrast')

    def test_read_t2(self):
        image = read_dicom_file(self.dicom_files["BRTUM014"])
        self._test_image_modality(image, "T2")


class TestDcm2Niix(TestCase):
    def setUp(self):
        dicom_directory = os.path.join("..", "..", "TEST", "TestDicoms")
        self.dataset = read_dicom_directory(dicom_directory, anonymize=True)

    def test_convert(self):
        in_dicom_file = os.path.join("..", "..", "TEST", "TestDicoms", "brain_001.dcm")
        nifti_file, sidecar_file = dcm2niix(in_dicom_file)
        image = nib.load(nifti_file)
        test_image = nib.load(os.path.join("..", "..", "TEST", "TestNiftis", "brain0.nii.gz"))
        self.assertEqual(image.header, test_image.header)

    def test_convert_dir_to_bids(self):
        self.assertEqual(self.dataset.get_number_of_subjects(), 3)
        self.assertEqual(len(self.dataset.get_image_paths()), 4)
        for subject in self.dataset.get_subjects():
            for session in subject.get_sessions():
                for group in session.get_groups():
                    for image in group.get_images():
                        self.assertEqual(image.get_extension(), ".nii.gz")

    def test_convert_to_bids(self):
        out_bids_dataset = os.path.join("..", "..", "TEST", "TestWriteBIDS")
        write_dataset(self.dataset, out_bids_dataset)
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-01", "dwi",
                                       "sub-01_ses-01_dwi.nii.gz")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-01", "dwi",
                                       "sub-01_ses-01_dwi.bval")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-01", "dwi",
                                       "sub-01_ses-01_dwi.bvec")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-01", "dwi",
                                       "sub-01_ses-01_dwi.json")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-02", "anat",
                                                    "sub-03_ses-02_FLAIR.nii.gz")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-02", "anat",
                                                    "sub-03_ses-02_FLAIR.json")))
        shutil.rmtree(out_bids_dataset)
