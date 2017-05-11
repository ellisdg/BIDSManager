from unittest import TestCase

from bids.base.image import Image, FunctionalImage


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
