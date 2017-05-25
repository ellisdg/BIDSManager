import glob
import os

from ..base.session import Session
from ..read.group_reader import read_group
from ..read.image_reader import parse_generic_name
from ..utils.utils import read_tsv


def load_groups(path_to_session_folder, metadata=None):
    return [read_group(group_folder, metadata=metadata) for group_folder
            in glob.glob(os.path.join(path_to_session_folder, "*"))]


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


def read_scans_metadata(path_to_sessoin_folder, subject_id, session_name):
    metadata_file = os.path.join(path_to_sessoin_folder, "sub-{0}_ses-{1}_scans.tsv".format(subject_id, session_name))
    if os.path.isfile(metadata_file):
        return read_tsv(metadata_file)
