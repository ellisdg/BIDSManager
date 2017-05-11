from unittest import TestCase

from bids.base.image import Image


class TestImage(TestCase):
    def test_change_acquisition(self):
        image = Image(modality="T1w", acquisition="contrast")
        basename = image.get_basename()

        image.set_acquisition("postcontrast")
        self.assertEqual(basename.replace("contrast", "postcontrast"), image.get_basename())
