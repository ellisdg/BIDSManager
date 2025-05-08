import glob
import os
import shutil
import warnings
from unittest import TestCase
import unittest

from bidsmanager.read.dicom_reader import  convert_dicom_directory, random_hash
from bidsmanager.write.dataset_writer import write_dataset


class TestDcm2Niix(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestDcm2Niix, cls).setUpClass()
        cls._dicom_directory = os.path.abspath("TestDicoms")
        # Create directory if it doesn't exist
        if not os.path.exists(cls._dicom_directory):
            os.makedirs(cls._dicom_directory)

        # create dicom files
        import pydicom
        import numpy as np
        from pydicom.dataset import Dataset, FileDataset
        import datetime

        subject_id = "AAA-555"

        for series_description in ("__other__",
                                   "3-Plane Loc",
                                   "T1 MPRAGE",
                                   "T2 Space_ND",
                                   "T2 Space",
                                   "GRE Field Mapping (L-R)",
                                   "GRE Field Mapping (R-L)",
                                   "rs-fMRI"):
            file_meta = pydicom.Dataset()
            filename = os.path.join(cls._dicom_directory, random_hash(), random_hash()) + ".dcm"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            ds = FileDataset(filename, {}, preamble=b"\0" * 128, file_meta=file_meta)

            # Set required file meta information for MRI images
            file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
            file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

            # Set essential DICOM attributes
            ds.PatientName = subject_id
            ds.PatientID = subject_id
            ds.SeriesDescription = series_description

            # Set date and time
            dt = datetime.datetime.now()
            ds.ContentDate = dt.strftime('%Y%m%d')
            ds.ContentTime = dt.strftime('%H%M%S')

            # Set other required attributes
            ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.StudyInstanceUID = pydicom.uid.generate_uid()
            ds.SeriesInstanceUID = pydicom.uid.generate_uid()

            # Add some additional attributes
            ds.InstitutionName = "Test Institution"
            ds.StudyDate = dt.strftime('%Y%m%d')
            ds.StudyTime = dt.strftime('%H%M%S')
            ds.EchoTime = 0.03
            ds.RepetitionTime = 2.0

            # Create random pixel data (small 16x16 array)
            pixel_array = np.random.randint(0, 1000, size=(16, 16), dtype=np.int16)
            ds.Rows = pixel_array.shape[0]
            ds.Columns = pixel_array.shape[1]
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
            ds.PixelRepresentation = 0
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.PixelData = pixel_array.tobytes()

            # Save the file
            ds.save_as(filename)

    @classmethod
    def tearDownClass(cls):
        # Clean up created files
        if os.path.exists(cls._dicom_directory):
            shutil.rmtree(cls._dicom_directory)
            pass
        super(TestDcm2Niix, cls).tearDownClass()



    def test_convert_to_bids(self):
        # create a heuristic for converting the dataset
        heuristic = {"SeriesDescription": (("T1", {"modality": "T1w"}),
                                           ("T2", {"modality": "T2w"}),
                                           ("Field", {"modality": "epi"}),
                                           ("fMRI", {"modality": "bold", "task": "rest"}),
                                           ("L-R", {"dir": "LR"}),
                                           ("R-L", {"dir": "RL"}),
                                           ("Loc", None),
                                           ("_ND", {"acq": "normalized"}))}

        # use the heuristic to convert the directory
        bids_directory = "TestDicomsBids"

        bids_dataset = convert_dicom_directory(self._dicom_directory,
                                               anonymize=True,
                                               heuristic=heuristic,
                                               bids_directory=bids_directory,
                                               delete_intermediates=True,
                                               verbose=True)


        self.assertTrue(bids_dataset.has_subject_id("AAA-555"))
        self.assertTrue(len(bids_dataset.get_subject("AAA-555").get_sessions()) == 1)
        self.assertEqual(len(bids_dataset.get_images(modality="T2w")), 2)
        self.assertEqual(len(bids_dataset.get_images(modality="epi")), 2)
        # check that multiple runs were handled correctly

        # check that fmaps were handled correctly

        # check that groups were assigned correctly based on the modality or just have the group assigned in the
        # heuristic
        shutil.rmtree("TestDicomsBids")

