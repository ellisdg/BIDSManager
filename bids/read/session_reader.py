import glob
import os

from ..base.session import Session
from ..read.group_reader import read_group


class SessionReader(object):
    def read_session(self, path_to_session_folder):
        session_name = self.parse_session_name(path_to_session_folder)
        session = Session(name=session_name, path=path_to_session_folder)
        for group in self.load_groups(path_to_session_folder):
            session.add_group(group)
        return session

    def parse_session_name(self, path_to_session_folder):
        return os.path.basename(path_to_session_folder).lstrip("ses-")

    def load_groups(self, path_to_session_folder):
        return [read_group(group_folder) for group_folder in glob.glob(os.path.join(path_to_session_folder, "*"))]


def read_session(path_to_session_folder):
    return SessionReader().read_session(path_to_session_folder)
