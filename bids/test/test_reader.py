import glob
import os
from unittest import TestCase

from ..reader import Reader


class TestReaderDataSet001(TestCase):
    def setUp(self):
        self.reader = Reader()
        self.dataset = self.reader.load_data_set("../../BIDS-examples/ds001")

    def test_read_dataset_subjects(self):
        self.assertEqual(self.dataset.get_subject_ids(),
                         ["{0:02d}".format(num + 1) for num in range(self.dataset.get_number_of_subjects())])

    def test_list_subject_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths())
        test_paths = set(glob.glob("../../BIDS-examples/ds001/sub-01/*/*.nii.gz"))
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_anat_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths(group_name="anat"))
        test_paths = set(glob.glob("../../BIDS-examples/ds001/sub-01/anat/*.nii.gz"))
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_task_names(self):
        subject = self.dataset.get_subject("01")
        task_names = set(subject.get_task_names())
        test_task_names = {"balloonanalogrisktask"}
        self.assertEqual(task_names, test_task_names)


class TestReaderDataSet114(TestCase):
    def setUp(self):
        self.reader = Reader()
        self.dataset = self.reader.load_data_set("../../BIDS-examples/ds114")

    def test_list_subject_sessions(self):
        sessions = set(self.dataset.get_subject("01").get_session_names())
        test_sessions = {"retest", "test"}
        self.assertEqual(sessions, test_sessions)

    def test_list_session_groups(self):
        group_names = set(self.dataset.get_subject("02").get_session("retest").get_group_names())
        self.assertEqual(group_names, {"anat", "func", "dwi"})

    def test_get_dataset_summary(self):
        subjects = self.dataset.get_subjects()
        for subject in subjects:
            session_names = subject.get_session_names()
            self.assertEqual(set(session_names), {"test", "retest"})
            for session in subject.get_sessions():
                group_names = session.get_group_names()
                self.assertEqual(set(group_names), {"anat", "func", "dwi"})
                for group in session.get_groups():
                    modalities = group.get_modalities()
                    if group.get_name() == "func":
                        self.assertEqual(set(modalities), {"bold"})


class TestReaderTestDir(TestCase):
    def setUp(self):
        self.reader = Reader()
        self.dataset = self.reader.load_data_set("./test_dir")

    def test_get_session_names(self):
        session_names = self.dataset.get_subject("01").get_session_names()
        self.assertEqual(set(session_names), {"test", "retest"})

    def test_get_session_path(self):
        session = self.dataset.get_subject("01").get_session("retest")
        self.assertEqual(session.get_path(), os.path.abspath("./test_dir/sub-01/ses-retest"))
