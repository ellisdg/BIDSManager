import unittest
from unittest import TestCase
from bids.base.session import Session
from bids.base.group import Group


class TestSession(TestCase):

    def test_add_group(self):
        session = Session()
        session.add_group(Group())


if __name__ == "__main__":
    unittest.main()
