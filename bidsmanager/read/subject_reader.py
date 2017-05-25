import glob
import os

from ..base.subject import Subject
from ..read.session_reader import read_session
from ..read.image_reader import parse_generic_name
from ..utils.utils import read_tsv


def parse_subject_id(path_to_subject):
    return parse_generic_name(path_to_subject, "sub")


def read_subject(path_to_subject, metadata=None):
    subject_id = parse_subject_id(path_to_subject)
    subject = Subject(subject_id, metadata=get_subject_metadata(metadata, subject_id))
    session_folders = glob.glob(os.path.join(path_to_subject, "ses-*"))
    add_session_folders(session_folders, subject, path_to_subject)
    return subject


def add_session_folders(session_folders, subject, path_to_subject):
    sessions_metadata = read_sessions_metadata(path_to_subject, subject.get_id())
    if session_folders:
        for session_folder in session_folders:
            session = read_session(session_folder, metadata=sessions_metadata)
            subject.add_session(session)
    else:
        session = read_session(path_to_subject, metadata=sessions_metadata)
        subject.add_session(session)


def read_sessions_metadata(path_to_subject, subject_id):
    meta_data_file = os.path.join(path_to_subject, "sub-{0}_sessions.tsv".format(subject_id))
    if os.path.isfile(meta_data_file):
        return read_tsv(meta_data_file)


def get_subject_metadata(metadata, subject_id):
    if metadata:
        return metadata["sub-{0}".format(subject_id)]
