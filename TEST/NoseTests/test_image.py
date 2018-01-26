import os
from unittest import TestCase

from bidsmanager.base.image import Image, FunctionalImage
from bidsmanager.read.image_reader import read_image_from_bids_path


def touch(tmp_file):
    with open(tmp_file, "w") as opened_file:
        print("creating: " + tmp_file)
        return opened_file


class TestImage(TestCase):
    def test_change_acquisition(self):
        image = Image(modality="T1w", acquisition="contrast")
        basename = image.get_basename()
        image.set_acquisition("postcontrast")
        self.assertEqual(basename.replace("contrast", "postcontrast"), image.get_basename())

    def test_change_task_name(self):
        image = FunctionalImage(modality="bold", task_name="prediction", run_number=3)
        basename = image.get_basename()
        image.set_task_name("weatherprediction")
        self.assertEqual(basename.replace("prediction", "weatherprediction"), image.get_basename())

    def test_write_changed_acquisition(self):
        tmp_file = "run-05_FLAIR.nii.gz"
        touch(tmp_file)
        new_tmp_file = "acq-contrast_" + tmp_file
        self.assertTrue(os.path.exists(tmp_file))
        try:
            image = read_image_from_bids_path(tmp_file)
            image.set_acquisition("contrast")
            image.update(move=True)
            self.assertFalse(os.path.exists(tmp_file))
            self.assertTrue(os.path.exists(new_tmp_file))
            os.remove(new_tmp_file)
        except AssertionError as error:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            if os.path.exists(new_tmp_file):
                os.remove(new_tmp_file)
            raise error
