import unittest
from unittest import TestCase
from bidsmanager import DataSet
from bidsmanager import Subject


class TestDataSet(TestCase):
    def test_add_subject(self):
        dataset = DataSet()
        dataset.add_subject(Subject())

    def test_number_of_subjects(self):
        subjects = [Subject("001"), Subject("002")]
        dataset = DataSet(subjects=subjects)
        self.assertEqual(dataset.get_number_of_subjects(), 2)

    def test_enforce_unique_ids(self):
        dataset = DataSet()
        subject_1 = Subject("001")
        dataset.add_subject(subject_1)
        subject_2 = Subject("001")
        with self.assertRaises(KeyError):
            dataset.add_subject(subject_2)

    def test_default_metadata(self):
        dataset = DataSet("test_dataset")
        metadata = dataset.get_metadata()
        self.assertEqual(metadata["Name"], "test_dataset")
        self.assertIsNotNone(metadata["BIDSVersion"])


if __name__ == "__main__":
    unittest.main()
