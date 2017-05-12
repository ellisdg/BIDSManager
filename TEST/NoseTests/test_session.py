import unittest
from unittest import TestCase
from bidsmanager.base.session import Session
from bidsmanager.base.group import Group
from bidsmanager.utils.session_utils import modality_to_group_name


class TestSession(TestCase):

    def test_add_group(self):
        session = Session()
        session.add_group(Group())

    def test_modality_to_group_name(self):
        self.assertEqual(modality_to_group_name("T2w"), "anat")


if __name__ == "__main__":
    unittest.main()
