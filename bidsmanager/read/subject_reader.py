import glob
import os

from ..base.subject import Subject
from ..read.session_reader import read_session
from ..read.image_reader import parse_generic_name


class SubjectReader(object):
    def read_subject(self, path_to_subject):
        subject_id = self.parse_subject_id(path_to_subject)
        subject = Subject(subject_id)
        session_folders = glob.glob(os.path.join(path_to_subject, "ses-*"))
        contains_sessions = any(["ses-" == os.path.basename(folder)[:4] for folder in session_folders])
        if contains_sessions:
            for session_folder in session_folders:
                session = read_session(session_folder)
                subject.add_session(session)
        else:
            session = read_session(path_to_subject)
            subject.add_session(session)
        return subject

    def parse_subject_id(self, path_to_subject):
        return parse_generic_name(path_to_subject, "sub")


def read_subject(path_to_subject_folder):
    return SubjectReader().read_subject(path_to_subject_folder)
