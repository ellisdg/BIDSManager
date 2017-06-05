import glob
import os
import shutil
import warnings
from unittest import TestCase

import nibabel as nib
import numpy as np

from bidsmanager.read import read_dicom_directory, read_dataset
from bidsmanager.read.dicom_reader import dcm2niix, dcm2niix_dwi
from bidsmanager.write.dataset_writer import write_dataset


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
        from bidsmanager.read.dicom_reader import get_dicom_set
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
        # rename an image task name
        image.set_task_name("lefthandfingertapping")
        # test that the image does not yet exist
        self.assertFalse(os.path.exists(os.path.join(out_bids_dataset, "sub-03", "ses-01", "func",
                                                     "sub-03_ses-01_task-lefthandfingertapping_bold.nii.gz")))
        # update the data set
        self.dataset.update(move=True)
        # test that the image now exists with the new task name
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
        final_bids_dataset.update()

        # test moving an image
        image = final_bids_dataset.get_images(acquisition="contrast")[1]
        # rename an image task name
        image.set_acquisition("postcontrast")
        # test that the image does not yet exist
        self.assertEqual(len(glob.glob(os.path.join(out_bids_dataset, "*", "*", "anat", "*acq-postcontrast*.nii.gz"))),
                         0)
        # update the data set
        final_bids_dataset.update(move=True)
        # test that the image now exists with the acquisition
        self.assertTrue(os.path.exists(glob.glob(os.path.join(out_bids_dataset, "*", "*", "anat",
                                                              "*acq-postcontrast*.nii.gz"))[0]))

        shutil.rmtree(out_bids_dataset)

    def test_invalid_key_modification(self):
        self.assertRaises(KeyError, self.dataset.modify_key, "01", "02")