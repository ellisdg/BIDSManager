from unittest import TestCase
from ..reader import Reader
import glob


class TestReaderDataSet001(TestCase):
    def setUp(self):
        self.reader = Reader()
        self.dataset = self.reader.load_data_set("../../BIDS-examples/ds001")

    def test_read_dataset_subjects(self):
        self.assertEqual(self.dataset.list_subject_ids(),
                         ["{0:02d}".format(num + 1) for num in range(self.dataset.get_number_of_subjects())])

    def test_list_subject_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.list_image_paths())
        test_paths = set(glob.glob("../../BIDS-examples/ds001/sub-01/*/*.nii.gz"))
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_anat_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.list_image_paths(group_name="anat"))
        test_paths = set(glob.glob("../../BIDS-examples/ds001/sub-01/anat/*.nii.gz"))
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_task_names(self):
        subject = self.dataset.get_subject("01")
        task_names = set(subject.list_task_names())
        test_task_names = {"balloonanalogrisktask"}
        self.assertEqual(task_names, test_task_names)



