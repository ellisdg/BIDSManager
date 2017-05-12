import glob
import os
import shutil
from unittest import TestCase


from bidsmanager.write.dataset_writer import write_dataset
from bidsmanager.read import read_csv, read_dataset
from test_reader import get_unorganized_example_directory


class TestWrite(TestCase):
    def setUp(self):
        self.dataset = read_csv(os.path.join(get_unorganized_example_directory(), "data_dict.csv"))
        self._dir = os.path.abspath("temp_dir")

    def tearDown(self):
        shutil.rmtree(self._dir)

    def test_write_dataset(self):
        self.bids_dataset = write_dataset(self.dataset, self._dir)
        self.assertEqual(set([os.path.basename(f) for f in glob.glob(os.path.join(self._dir, "*"))]),
                         {"sub-003", "sub-007", "sub-005"})
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
        self.assertEqual(len(reread_dataset.get_images(task_name="fingertapping")), 0)
        self.assertEqual(len(reread_dataset.get_images(task_name="ft")), len(fingertapping_images))
