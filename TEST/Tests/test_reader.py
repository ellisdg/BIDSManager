import glob
import os
import sqlite3
from unittest import TestCase
from datetime import date, datetime

from bidsmanager import read_dataset, read_csv
from bidsmanager.read.image_reader import read_image


def get_script_directory():
    return os.path.dirname(os.path.abspath(__file__))


def get_test_directory():
    return os.path.dirname(get_script_directory())


def get_bids_examples_directory():
    return os.path.join(get_test_directory(), "BIDS-examples")


def get_example_directory():
    return os.path.join(get_script_directory(), "example_bids_dir")


def get_unorganized_example_directory():
    return os.path.join(get_script_directory(), "unorganized_example_dir")


class TestReaderDataSet001(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestReaderDataSet001, cls).setUpClass()
        cls.dataset = read_dataset(os.path.join(get_bids_examples_directory(), "ds001"))

    def test_read_dataset_subjects(self):
        self.assertEqual(self.dataset.get_subject_ids(),
                         ["{0:02d}".format(num + 1) for num in range(self.dataset.get_number_of_subjects())])

    def test_list_subject_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths())
        test_paths = set([os.path.abspath(f) for f in glob.glob(os.path.join(get_bids_examples_directory(),
                                                                             "ds001", "sub-01", "*", "*.nii.gz"))])
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_anat_scans(self):
        subject = self.dataset.get_subject("01")
        scan_paths = set(subject.get_image_paths(group_name="anat"))
        test_paths = set([os.path.abspath(f) for f in glob.glob(os.path.join(get_bids_examples_directory(),
                                                                             "ds001", "sub-01", "anat", "*.nii.gz"))])
        self.assertEqual(scan_paths, test_paths)

    def test_list_subject_task_names(self):
        subject = self.dataset.get_subject("01")
        task_names = set(subject.get_task_names())
        test_task_names = {"balloonanalogrisktask"}
        self.assertEqual(task_names, test_task_names)

    def test_get_images_with_task_name(self):
        self.assertEqual(os.path.basename(self.dataset.get_image_paths(task="balloonanalogrisktask",
                                                                       subject_id="01", run="01")[0]),
                         "sub-01_task-balloonanalogrisktask_run-01_bold.nii.gz")

    def test_list_all_t1_scans(self):
        t1_images = self.dataset.get_image_paths(modality="T1w")
        t1_glob_list = [os.path.abspath(f) for f in glob.glob(os.path.join(get_bids_examples_directory(),
                                                                           "ds001", "sub-*", "anat", "*T1w.nii.gz"))]
        self.assertEqual(sorted(t1_images), sorted(t1_glob_list))

    def test_dataset_path(self):
        self.assertEqual(os.path.join(get_bids_examples_directory(), "ds001"), self.dataset.get_path())

    def test_sql_interface_exists(self):
        sql_file = os.path.join(get_test_directory(), "ds001.sql")
        self.dataset.create_sql_interface(sql_file)
        self.assertTrue(os.path.isfile(sql_file))

        # connect to the sql database to ensure it has all the proper elements
        connection = sqlite3.connect(sql_file)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Subject")
        self.assertEqual(len(cursor.fetchall()), 16)

        cursor.execute("SELECT * FROM Image")
        self.assertEqual(len(cursor.fetchall()), 16 * 5)

        cursor.execute("SELECT * FROM Session")
        self.assertEqual(len(cursor.fetchall()), 0)

        cursor.execute("SELECT * FROM Image WHERE modality='bold'")
        self.assertEqual(len(cursor.fetchall()), 16 * 3)

        cursor.execute("SELECT * FROM Image WHERE task_name='balloonanalogrisktask'")
        self.assertEqual(len(cursor.fetchall()), 16 * 3)

        os.remove(sql_file)

    def test_read_metadata(self):
        self.assertEqual(self.dataset.get_subject("11").get_metadata("age"), 24)
        self.assertEqual(self.dataset.get_subject("04").get_metadata("sex"), "F")
        self.assertEqual(self.dataset.get_metadata("Name"), "Balloon Analog Risk Task")

    def test_lazy_load_metadata(self):
        self.assertFalse(self.dataset._metadata)
        self.assertEqual(self.dataset.get_metadata("Name"), "Balloon Analog Risk Task")
        self.assertTrue(self.dataset._metadata)

        # Can't figure out lazy loading of subjects and session metadata
        # self.assertFalse(self.dataset.get_subject("11")._metadata)
        # self.assertEqual(self.dataset.get_subject("11").get_metadata("age"), 24)
        # self.assertTrue(self.dataset.get_subject("11")._metadata)


class TestReaderDataSet114(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestReaderDataSet114, cls).setUpClass()
        cls.ds_path = os.path.join(get_bids_examples_directory(), "ds114")
        cls.dataset = read_dataset(cls.ds_path)

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

    def test_sql_interface(self):
        sql_file = os.path.join(get_test_directory(), "ds114.sql")
        self.dataset.create_sql_interface(sql_file)
        self.assertTrue(os.path.isfile(sql_file))

        # connect to the sql database to ensure it has all the proper elements
        connection = sqlite3.connect(sql_file)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Session")
        self.assertEqual(len(cursor.fetchall()), 10 * 2)

        cursor.execute("SELECT Image.modality FROM Image JOIN Session ON Image.session_id=Session.id "
                       "AND Session.name='test'")
        self.assertEqual(len(cursor.fetchall()), 10 * 7)

        cursor.execute("SELECT Image.modality FROM Image JOIN Session JOIN Subject ON Image.session_id=Session.id "
                       "AND Session.name='test' AND Session.subject_id=Subject.id AND Subject.name='01'")
        self.assertEqual(len(cursor.fetchall()), 7)

        cursor.execute("SELECT Image.path FROM Image")
        self.assertEqual(set(self.dataset.get_image_paths()), set([row[0] for row in cursor.fetchall()]))

        cursor.execute("SELECT Image.path FROM Image WHERE Image.group_name='anat';")
        self.assertEqual(set(self.dataset.get_image_paths(group_name="anat")),
                         set([row[0] for row in cursor.fetchall()]))

        os.remove(sql_file)

    def test_subject_path(self):
        subject = self.dataset.get_subject("05")
        self.assertEqual(os.path.join(self.ds_path, "sub-05"), subject.get_path())


class TestReaderTestDir(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestReaderTestDir, cls).setUpClass()
        cls.dataset = read_dataset(get_example_directory())

    def test_get_session_names(self):
        session_names = self.dataset.get_subject("01").get_session_names()
        self.assertEqual(set(session_names), {"test", "retest"})

    def test_get_session_path(self):
        session = self.dataset.get_subject("01").get_session("retest")
        self.assertEqual(session.get_path(), os.path.abspath(os.path.join(get_example_directory(),
                                                                          "sub-01", "ses-retest")))

    def test_get_group_path(self):
        group = self.dataset.get_subject("01").get_session("retest").get_group("anat")
        self.assertEqual(group.get_path(), os.path.abspath(os.path.join(get_example_directory(),
                                                                        "sub-01", "ses-retest", "anat")))

    def test_get_t1_contrast_image_paths(self):
        image_paths_glob = [os.path.abspath(f) for f in
                            glob.glob(os.path.join(get_example_directory(),
                                                   "sub-*", "ses-*", "*", "*acq-contrast*.nii.gz"))]
        image_paths = self.dataset.get_image_paths(acq="contrast", modality="T1w")
        image_paths_from_images = [image.get_path() for image in self.dataset.get_images(acq="contrast",
                                                                                         modality="T1w")]
        self.assertEqual(sorted(image_paths_glob), sorted(image_paths))
        self.assertEqual(sorted(image_paths), sorted(image_paths_from_images))

    def test_meta_data(self):
        subject = self.dataset.get_subject("01")
        self.assertEqual(date(year=1888, day=12, month=3), subject.get_metadata("dob"))
        self.assertEqual("John Doe", subject.get_metadata("name"))
        self.assertEqual(date(year=1995, month=6, day=1), subject.get_session("test").get_metadata("date"))
        self.assertEqual(self.dataset.get_image(subject_id="01",
                                                session="test",
                                                modality="T1w").get_metadata("Manufacturer"), "GE")
        self.assertEqual(self.dataset.get_image(subject_id="01",
                                                session="test",
                                                modality="T1w").get_metadata("acq_time"),
                         datetime(year=1877, month=6, day=15, hour=13, minute=45, second=30))

    def test_sql_metadata(self):
        sql_file = os.path.join(get_test_directory(), "example.sql")
        self.dataset.create_sql_interface(sql_file)
        self.assertTrue(os.path.isfile(sql_file))

        # connect to the sql database to ensure it has all the proper elements
        connection = sqlite3.connect(sql_file)
        cursor = connection.cursor()
        cursor.execute("SELECT Image.Manufacturer FROM Image JOIN Session ON Session.id=Image.session_id "
                       "AND Session.name='test' AND Image.Modality='T1w'")
        self.assertEqual(cursor.fetchall()[0][0], "GE")

        cursor.execute("SELECT Image.Manufacturer FROM Image JOIN Session ON Session.id=Image.session_id "
                       "AND Session.name='retest' AND Image.acquisition='contrast' AND Image.Modality='T1w'")
        self.assertEqual(cursor.fetchall()[0][0], "Philips")

        os.remove(sql_file)

    def test_get_no_acquisition(self):
        images = self.dataset.get_images(subject_id="01", session="retest", modality="T1w", acq=False)
        self.assertEqual(len(images), 1)

    def test_get_image(self):
        images = self.dataset.get_images(subject_id="01", session="retest", modality="T1w", acq=False)
        self.assertEqual(self.dataset.get_image(subject_id="01", session="retest", modality="T1w", acq=False),
                         images[0])
        self.assertRaises(RuntimeError, self.dataset.get_image)
        self.assertRaises(RuntimeError, self.dataset.get_image, session="retest")


class TestReaderCSV(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestReaderCSV, cls).setUpClass()
        cls.dataset = read_csv(os.path.join(get_unorganized_example_directory(), "data_dict.csv"))

    def test_read_subjects(self):
        subject_ids = self.dataset.get_subject_ids()
        self.assertEqual(set(subject_ids), {"003", "007", "005", "UNMC^001"})

    def test_read_sessions(self):
        self.assertEqual(set(self.dataset.get_subject("003").get_session_names()), {"visit1", "visit2"})

    def test_read_groups(self):
        self.assertEqual(set(self.dataset.get_subject("003").get_session("visit1").get_group_names()), {"anat", "func"})

    def test_read_images(self):
        self.assertEqual(set([os.path.abspath(f) for f in glob.glob(os.path.join(get_unorganized_example_directory(),
                                                                                 "*.nii.gz"))]),
                         set(self.dataset.get_image_paths()))

    def test_read_t1w_modality(self):
        self.assertEqual(set([os.path.abspath(os.path.join(get_unorganized_example_directory(), f)) for f in
                              {"t1.nii.gz", "some_t1.nii.gz", "some_other_t1.nii.gz", "third_t1.nii.gz",
                               "t1_from_different_subject.nii.gz", "i_dont_know.nii.gz", "second_t1.nii.gz",
                               "unmc_t1.nii.gz"}]),
                         set(self.dataset.get_image_paths(group_name="anat", modality="T1w")))

    def test_read_flair_modality(self):
        self.assertEqual({os.path.abspath(os.path.join(get_unorganized_example_directory(), "flair.nii.gz"))},
                         set(self.dataset.get_image_paths(modality="FLAIR")))

    def test_read_bold_image(self):
        image = self.dataset.get_subject("003").get_session("visit1").get_group("func").get_images()[0]
        self.assertEqual(image.get_task_name(), "fingertapping")

    def test_read_bold_group(self):
        group = self.dataset.get_subject("003").get_session("visit1").get_group("func")
        self.assertEqual(group.get_task_names(), ["fingertapping"])

    def test_read_multiple_runs(self):
        group = self.dataset.get_subject("003").get_session("visit2").get_group("anat")
        self.assertEqual([os.path.basename(f) for f in group.get_image_paths(run=3)], ["third_t1.nii.gz"])


class TestImageReader(TestCase):
    def test_overwrite_entities(self):
        image_path = os.path.join(get_unorganized_example_directory(), "fmri.nii.gz")
        image = read_image(image_path)
        self.assertIsNone(image.get_task_name())
        self.assertEqual(image.get_modality(), "fmri")
        custom_entities = {"modality": "bold", "task": "rest", "run": 2, "dir": "AP"}
        image = read_image(image_path, **custom_entities)
        for key, value in custom_entities.items():
            self.assertEqual(getattr(image, "get_" + key)(), value)
