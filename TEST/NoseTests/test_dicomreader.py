from unittest import TestCase
import gzip
import tarfile
import os
import glob
import shutil
import warnings
try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

import numpy as np
import nibabel as nib

from bids.read.dicom_reader import read_dicom_file, read_dicom_directory, dcm2niix, dcm2niix_dwi
from bids.read.dataset_reader import read_dataset
from bids.write.dataset_writer import write_dataset


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
    def setUpClass(cls):
        super(TestDicomReader, cls).setUpClass()
        cls.dicom_files = dict()
        TestDicomReader.setUpDicomFiles(cls.dicom_files)
        TestDicomReader.setUpFlair(cls.dicom_files)

    @staticmethod
    def setUpDicomFiles(dicom_files):
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
        image_file = read_dicom_file(self.dicom_files["MR-MONO2-16-head"]).get_path()
        test_image_file = os.path.join("TestNiftis", "MR-MONO2-16-head.nii.gz")
        self.assertEqual(nib.load(image_file).header, nib.load(test_image_file).header)

    def test_read_t1(self):
        image = read_dicom_file(self.dicom_files["BRTUM008"])
        self._test_image_modality(image, "T1w")
        self.assertEqual(image.get_acquisition(), 'contrast')

    def test_read_t2(self):
        image = read_dicom_file(self.dicom_files["BRTUM014"])
        self._test_image_modality(image, "T2w")


class TestDcm2Niix(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDcm2Niix, cls).setUpClass()
        dicom_directory = os.path.abspath("TestDicoms")
        cls.dataset = read_dicom_directory(dicom_directory, anonymize=True,
                                           skip_image_descriptions=["SENSE", "FS", "Ax", "MC"])

    def test_convert(self):
        in_dicom_file = os.path.join("TestDicoms", "brain_001.dcm")
        nifti_file, sidecar_file = dcm2niix(in_dicom_file)
        image = nib.load(nifti_file)
        test_image = nib.load(os.path.join("TestNiftis", "brain0.nii.gz"))
        self.assertEqual(image.header, test_image.header)

    def test_convert_dwi(self):
        warnings.simplefilter("error")
        from bids.read.dicom_reader import get_dicom_set
        dwi_dicoms = get_dicom_set(os.path.join("TestDicoms", "DTI_0544"))
        dwi_dicom_files = [dwi_dicom.get_path() for dwi_dicom in dwi_dicoms]
        self.assertRaises(RuntimeWarning, dcm2niix, in_file=dwi_dicom_files)
        dwi_files = dcm2niix_dwi(dwi_dicom_files)
        for dwi_file in dwi_files:
            self.assertFalse("ADC" in dwi_file)
        warnings.simplefilter("default")

    def test_convert_dir_to_bids(self):
        self.assertEqual(self.dataset.get_number_of_subjects(), 4)
        self.assertEqual(len(self.dataset.get_image_paths()), 7)
        for subject in self.dataset.get_subjects():
            for session in subject.get_sessions():
                for group in session.get_groups():
                    for image in group.get_images():
                        self.assertEqual(image.get_extension(), ".nii.gz")

    def test_convert_to_bids(self):
        out_bids_dataset = os.path.abspath("TestWriteBIDS")
        orig_file = self.dataset.get_image_paths(modality="T1w")[0]
        write_dataset(self.dataset, out_bids_dataset, move=True)
        self.assertFalse(os.path.exists(orig_file))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-04", "ses-01", "dwi",
                                       "sub-04_ses-01_dwi.nii.gz")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-04", "ses-01", "dwi",
                                       "sub-04_ses-01_dwi.bval")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-04", "ses-01", "dwi",
                                       "sub-04_ses-01_dwi.bvec")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-04", "ses-01", "dwi",
                                       "sub-04_ses-01_dwi.json")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-01", "func",
                                                    "sub-03_ses-01_task-lefthandft_bold.nii.gz")))
        # test moving an image
        image = self.dataset.get_images(subject_id="03", session="01", task_name="lefthandft")[0]
        image.set_task_name("lefthandfingertapping")
        self.assertFalse(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-01", "func",
                                                     "sub-03_ses-01_task-lefthandfingertapping_bold.nii.gz")))
        self.dataset.update(run=True, move=True)
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-01", "func",
                                                    "sub-03_ses-01_task-lefthandfingertapping_bold.nii.gz")))

        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-02", "anat",
                                                    "sub-01_ses-02_FLAIR.nii.gz")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-01", "ses-02", "anat",
                                                    "sub-01_ses-02_FLAIR.json")))
        self.assertTrue(os.path.exists(os.path.join(out_bids_dataset, "sub-04", "ses-02", "anat",
                                                    "sub-04_ses-02_acq-contrast_T1w.json")))
        test_dicom = os.path.abspath("TestDicoms/brain_401.dcm")
        test_nifti = os.path.abspath("TestNiftis/brain_401.nii.gz")
        dcm2niix(test_dicom, test_nifti)
        test_image = nib.load(test_nifti)
        bids_image = nib.load(
            self.dataset.get_image_paths(subject_id="02", session="01", acquisition="contrast")[0])
        self.assertTrue(np.all(test_image.get_data() == bids_image.get_data()))

        # test that the dataset can then be read
        final_bids_dataset = read_dataset(out_bids_dataset)
        self.assertEqual(final_bids_dataset.get_images(subject_id="01", session="01",
                                                       modality="FLAIR")[0].get_basename(),
                         "sub-01_ses-01_FLAIR.nii.gz")
        self.assertEqual(os.path.basename(final_bids_dataset.get_images(subject_id="04", session="01",
                                                                        modality="dwi")[0]._bval_path),
                         "sub-04_ses-01_dwi.bval")
        self.assertEqual(os.path.basename(final_bids_dataset.get_images(subject_id="04", session="01",
                                                                        modality="dwi")[0].sidecar_path),
                         "sub-04_ses-01_dwi.json")
        final_bids_dataset.update(run=True)
        shutil.rmtree(out_bids_dataset)

    def test_invalid_key_modification(self):
        self.assertRaises(KeyError, self.dataset.modify_key, "01", "02")
