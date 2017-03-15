import unittest
from unittest import TestCase
from bids.base.group import Group
from bids.base.image import Image


class TestGroup(TestCase):
    def setUp(self):
        self.group = Group()

    def test_add_image(self):
        image = Image()
        self.group.add_image(image)

if __name__ == '__main__':
    unittest.main()
