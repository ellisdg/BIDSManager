import glob
import os

from ..base.session import Session
from ..read.group_reader import read_group
from ..read.image_reader import parse_generic_name
from ..utils.utils import read_tsv


def load_groups(path_to_session_folder, metadata=None):
    groups = list()
    for group_folder in glob.glob(os.path.join(path_to_session_folder, "*")):
        if os.path.isdir(group_folder):
            groups.append(read_group(group_folder, metadata=metadata))
    return groups


def parse_session_name(path_to_session_folder):
    return parse_generic_name(path_to_session_folder, "ses")


def read_session(path_to_session_folder, subject_id, metadata=None):
    session_name = parse_session_name(path_to_session_folder)
    session = Session(name=session_name, path=path_to_session_folder,
                      metadata=get_session_metadata(metadata, session_name))
    for group in load_groups(path_to_session_folder, metadata=read_scans_metadata(path_to_session_folder, subject_id,
                                                                                  session_name)):
        session.add_group(group)
    return session


def get_session_metadata(metadata, session_name):
    if metadata:
        return metadata["ses-{0}".format(session_name)]


def read_scans_metadata(path_to_session_folder, subject_id, session_name=None):
    subject_basename = "sub-{}".format(subject_id)
    components = [subject_basename, "scans.tsv"]
    if session_name:
        session_basename = "ses-{}".format(session_name)
        components.insert(1, session_basename)
    metadata_file = os.path.join(path_to_session_folder, "_".join(components))
    if os.path.isfile(metadata_file):
        return read_tsv(metadata_file)
