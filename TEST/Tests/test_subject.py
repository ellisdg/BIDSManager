import unittest
from unittest import TestCase
from bidsmanager.base.session import Session
from bidsmanager.base.subject import Subject


class TestSubject(TestCase):
    def test_add_session(self):
        subject = Subject()
        subject.add_session(Session())

    def test_subject_name(self):
        name = "777"
        subject = Subject(name)
        self.assertTrue(name == subject.get_id())
        self.assertTrue(name == subject.get_name())
        self.assertTrue(name == subject.name)


if __name__ == "__main__":
    unittest.main()
