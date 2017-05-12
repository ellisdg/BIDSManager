import unittest
from unittest import TestCase
from bids.base.session import Session
from bids.base.subject import Subject


class TestSubject(TestCase):
    def test_add_session(self):
        subject = Subject()
        subject.add_session(Session())


if __name__ == "__main__":
    unittest.main()
