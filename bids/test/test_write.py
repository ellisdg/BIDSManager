import glob
import os
import shutil
from unittest import TestCase


from ..write.dataset_writer import write_dataset
from ..read import read_csv


class TestWrite(TestCase):
    def setUp(self):
        self.dataset = read_csv("./unorganized_example_dir/data_dict.csv")
        self._dir = os.path.abspath("./temp_dir")

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
