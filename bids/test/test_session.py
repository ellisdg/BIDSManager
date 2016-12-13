import unittest
from unittest import TestCase
from ..base.session import Session
from ..base.group import Group


class TestSession(TestCase):

    def test_add_group(self):
        session = Session()
        session.add_group(Group())


if __name__ == "__main__":
    unittest.main()
