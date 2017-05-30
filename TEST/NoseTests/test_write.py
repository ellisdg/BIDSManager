import glob
import os
import shutil
from unittest import TestCase
import random

from bidsmanager.write.dataset_writer import write_dataset
from bidsmanager.read import read_csv, read_dataset
from bidsmanager.utils.utils import read_json
from test_reader import get_unorganized_example_directory


class TestWrite(TestCase):
    def setUp(self):
        self.dataset = read_csv(os.path.join(get_unorganized_example_directory(), "data_dict.csv"))
        self._dir = os.path.abspath("temp_dir")

    def tearDown(self):
        shutil.rmtree(self._dir)

    def test_write_dataset(self):
        self.bids_dataset = write_dataset(self.dataset, self._dir)
        subject_ids = {"sub-003", "sub-007", "sub-005", "sub-UNMC001"}
        self.assertEqual(set([os.path.basename(f) for f in glob.glob(os.path.join(self._dir, "sub-*"))]),
                         subject_ids)
        self.assertEqual(set([os.path.basename(f) for f in glob.glob(os.path.join(self._dir, "sub-007", "*"))]),
                         {"ses-visit1", "ses-visit3"})
        self.assertEqual(set([os.path.basename(f) for f in glob.glob(os.path.join(self._dir, "sub-005", "ses-visit2",
                                                                                  "*"))]),
                         {"anat"})
        self.assertEqual(set([os.path.basename(f) for f in glob.glob(os.path.join(self._dir, "sub-003", "ses-visit1",
                                                                                  "*", "*.nii.gz"))]),
                         {"sub-003_ses-visit1_task-fingertapping_bold.nii.gz", "sub-003_ses-visit1_FLAIR.nii.gz",
                          "sub-003_ses-visit1_T1w.nii.gz"})

        fingertapping_images = self.dataset.get_images(task_name="fingertapping")
        for image in fingertapping_images:
            image.set_task_name("ft")
        self.dataset.update(run=True, move=True)

        reread_dataset = read_dataset(self._dir)
        self.assertEqual(set(["sub-" + sid for sid in reread_dataset.get_subject_ids()]), subject_ids)
        self.assertEqual(len(reread_dataset.get_images(task_name="fingertapping")), 0)
        self.assertEqual(len(reread_dataset.get_images(task_name="ft")), len(fingertapping_images))


class TestWriteMetaData(TestCase):
    def test_save_ds001_metadata(self):
        dataset = read_dataset(os.path.abspath("./BIDS-examples/ds001"))

        test_answers = dict()

        for subject in dataset.get_subjects():
            random_int = random.randint(0, 100)
            subject.add_metadata("random_int", random_int)
            test_answers[subject.get_id()] = random_int

        out_dir = os.path.abspath("./tmp/custom_ds001")
        write_dataset(dataset=dataset, output_dir=out_dir, move=False)

        test_dataset = read_dataset(out_dir)
        for subject in test_dataset.get_subjects():
            self.assertEquals(subject.get_metadata("random_int"), test_answers[subject.get_id()])

        new_json = os.path.join(test_dataset.get_path(), "dataset_description.json")
        self.assertTrue(os.path.exists(new_json))
        self.assertEquals(dataset.get_metadata(), read_json(new_json))

        shutil.rmtree(out_dir)
