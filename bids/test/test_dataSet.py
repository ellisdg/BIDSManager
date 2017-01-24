import unittest
from unittest import TestCase
from bids.base.dataset import DataSet
from bids.base.subject import Subject


class TestDataSet(TestCase):
    def test_add_subject(self):
        dataset = DataSet()
        dataset.add_subject(Subject())

    def test_number_of_subjects(self):
        dataset = DataSet(subjects=[Subject("001"), Subject("002")])
        self.assertEqual(dataset.get_number_of_subjects(), 2)

    def test_enforce_unique_ids(self):
        dataset = DataSet()
        subject_1 = Subject("001")
        dataset.add_subject(subject_1)
        subject_2 = Subject("001")
        with self.assertRaises(KeyError):
            dataset.add_subject(subject_2)

if __name__ == "__main__":
    unittest.main()