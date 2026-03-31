import unittest
from unittest import TestCase
from datetime import datetime
from bidsmanager.base.group import Group
from bidsmanager.base.image import Image


class TestGroup(TestCase):
    def setUp(self):
        self.group = Group()

    def test_add_image(self):
        image = Image()
        self.group.add_image(image)

    def test_normalize_runs_for_write_preserves_existing_order(self):
        late = Image(modality="T1w")
        late.add_metadata("AcquisitionTime", datetime(2024, 1, 1, 9, 0, 0))
        early = Image(modality="T1w")
        early.add_metadata("AcquisitionTime", datetime(2024, 1, 1, 8, 0, 0))

        self.group.add_image(late)
        self.group.add_image(early)

        self.group.normalize_runs_for_write()

        images = self.group.get_all_images()
        self.assertEqual([image.get_metadata("AcquisitionTime") for image in images], [
            datetime(2024, 1, 1, 9, 0, 0),
            datetime(2024, 1, 1, 8, 0, 0),
        ])
        self.assertEqual([image.get_run_number() for image in images], [1, 2])

if __name__ == '__main__':
    unittest.main()
