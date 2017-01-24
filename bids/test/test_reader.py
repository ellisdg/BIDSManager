import glob
import os
from unittest import TestCase

from ..read import DataSetReader, read_dataset
from bids.read import read_csv


class TestReaderDataSet001(TestCase):
    def setUp(self):
        self.reader = DataSetReader()
        self.dataset = self.reader.load_data_set("../../BIDS-examples/ds001")

    def test_read_dataset_subjects(self):
        self.assertEqual(self.dataset.get_subject_ids(),
                         ["{0:02d}".format(num + 1) for num in range(self.dataset.get_number_of_subjects())])

    def test_list_subject_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths())
        test_paths = set([os.path.abspath(f) for f in glob.glob("../../BIDS-examples/ds001/sub-01/*/*.nii.gz")])
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_anat_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths(group_name="anat"))
        test_paths = set([os.path.abspath(f) for f in glob.glob("../../BIDS-examples/ds001/sub-01/anat/*.nii.gz")])
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_task_names(self):
        subject = self.dataset.get_subject("01")
        task_names = set(subject.get_task_names())
        test_task_names = {"balloonanalogrisktask"}
        self.assertEqual(task_names, test_task_names)

    def test_list_all_t1_scans(self):
        t1_images = self.dataset.get_image_paths(modality="T1w")
        t1_glob_list = [os.path.abspath(f) for f in glob.glob("../../BIDS-examples/ds001/sub-*/anat/*T1w.nii.gz")]
        self.assertEqual(sorted(t1_images), sorted(t1_glob_list))


class TestReaderDataSet114(TestCase):
    def setUp(self):
        self.reader = DataSetReader()
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
        self.dataset = read_dataset("./example_bids_dir")

    def test_get_session_names(self):
        session_names = self.dataset.get_subject("01").get_session_names()
        self.assertEqual(set(session_names), {"test", "retest"})

    def test_get_session_path(self):
        session = self.dataset.get_subject("01").get_session("retest")
        self.assertEqual(session.get_path(), os.path.abspath("./example_bids_dir/sub-01/ses-retest"))

    def test_get_group_path(self):
        group = self.dataset.get_subject("01").get_session("retest").get_group("anat")
        self.assertEqual(group.get_path(), os.path.abspath("./example_bids_dir/sub-01/ses-retest/anat"))

    def test_get_t1_contrast_image_paths(self):
        image_paths_glob = [os.path.abspath(f) for f in
                            glob.glob("./example_bids_dir/sub-*/ses-*/*/*acq-contrast*.nii.gz")]
        image_paths = self.dataset.get_image_paths(acquisition="contrast", modality="T1w")
        self.assertEqual(sorted(image_paths_glob), sorted(image_paths))


class TestReaderCSV(TestCase):
    def setUp(self):
        self.dataset = read_csv("./unorganized_example_dir/data_dict.csv")

    def test_read_subjects(self):
        subject_ids = self.dataset.get_subject_ids()
        self.assertEqual(set(subject_ids), {'003', '007', '005'})

    def test_read_sessions(self):
        self.assertEqual(set(self.dataset.get_subject('003').get_session_names()), {'visit1', 'visit2'})

    def test_read_groups(self):
        self.assertEqual(set(self.dataset.get_subject('003').get_session('visit1').get_group_names()), {'anat', 'func'})

    def test_read_images(self):
        self.assertEqual(set([os.path.abspath(f) for f in glob.glob('./unorganized_example_dir/*.nii.gz')]),
                         set(self.dataset.get_image_paths()))

    def test_read_t1w_modality(self):
        self.assertEqual(set([os.path.abspath(os.path.join('./unorganized_example_dir', f)) for f in
                              {'t1.nii.gz', 'some_t1.nii.gz', 'some_other_t1.nii.gz', 'third_t1.nii.gz',
                               't1_from_different_subject.nii.gz', 'i_dont_know.nii.gz', 'second_t1.nii.gz'}]),
                         set(self.dataset.get_image_paths(modality='T1w')))

    def test_read_flair_modality(self):
        self.assertEqual({os.path.abspath('./unorganized_example_dir/flair.nii.gz')},
                         set(self.dataset.get_image_paths(modality="FLAIR")))

    def test_read_bold_image(self):
        image = self.dataset.get_subject('003').get_session('visit1').get_group('func').get_images()[0]
        self.assertEqual(image.get_task_name(), "Finger Tapping")

    def test_read_bold_group(self):
        group = self.dataset.get_subject('003').get_session('visit1').get_group('func')
        self.assertEqual(group.get_task_names(), ['Finger Tapping'])

    def test_read_mulitple_runs(self):
        group = self.dataset.get_subject('003').get_session('visit2').get_group('anat')
        self.assertEqual([os.path.basename(f) for f in group.get_image_paths(run_number=3)], ['third_t1.nii.gz'])
