from base.dataset import DataSet
from base.subject import Subject
from base.image import Image
from creator import GroupCreator
from base.session import Session
import glob
import os


class Reader(object):
    def __init__(self):
        super(Reader, self).__init__()

    def load_data_set(self, path_to_data_set):
        return DataSet(self.get_subject_subjects(path_to_data_set))

    def get_subject_subjects(self, path_to_data_set):
        return [self.load_subject(path_to_subject) for path_to_subject in self.find_subject_folders(path_to_data_set)]

    def find_subject_folders(self, path_to_data_set):
        return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))

    def load_subject(self, path_to_subject):
        subject = Subject(os.path.basename(path_to_subject).lstrip("sub-"))
        session_folders = glob.glob(os.path.join(path_to_subject, "*"))
        contains_sessions = any(["ses-" == os.path.basename(folder)[:4] for folder in session_folders])
        if contains_sessions:
            for session_folder in session_folders:
                session = read_session(session_folder)
                subject.add_session(session)
        else:
            session = read_session(path_to_subject)
            subject.add_session(session)
        return subject


class SessionReader(object):
    def __init__(self, path_to_session_folder):
        self.path_to_sesion_folder = path_to_session_folder
        session_name = os.path.basename(self.path_to_sesion_folder).lstrip("ses-")
        self.session = Session(session_name)
        for group in self.load_groups():
            self.session.add_group(group)

    def load_groups(self):
        return [read_group(group_folder) for group_folder in glob.glob(os.path.join(self.path_to_sesion_folder, "*"))]

    def get_session(self):
        return self.session


class GroupReader(object):
    def __init__(self):
        self.group_creator = GroupCreator()

    def load_group(self, path_to_group_folder):
        return self.group_creator.create_group(self.parse_group_name(path_to_group_folder),
                                               self.read_images(path_to_group_folder))

    def parse_group_name(self, path_to_group_folder):
        return os.path.basename(path_to_group_folder)

    def read_images(self, path_to_group_folder):
        images = []
        for image_file in glob.glob(os.path.join(path_to_group_folder, "*.nii*")):
            images.append(Image(image_file))
        return images


def read_group(path_to_group_folder):
    reader = GroupReader()
    return reader.load_group(path_to_group_folder)


def read_session(path_to_session_folder):
    reader = SessionReader(path_to_session_folder)
    return reader.get_session()
