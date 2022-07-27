import unittest
from unittest import TestCase
from bidsmanager.base.session import Session
from bidsmanager.base.subject import Subject


class TestSubject(TestCase):
    def test_add_session(self):
        subject = Subject()
        subject.add_session(Session())


if __name__ == "__main__":
    unittest.main()
