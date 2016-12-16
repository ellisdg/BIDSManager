from base.dataset import DataSet
from base.subject import Subject
from base.image import Image, FunctionalImage
from base.group import Group, FunctionalGroup
from base.session import Session
import glob
import os
import re


class Reader(object):
    def load_data_set(self, path_to_data_set):
        return DataSet(self.get_subject_subjects(path_to_data_set))

    def get_subject_subjects(self, path_to_data_set):
        return [read_subject(path_to_subject) for path_to_subject in self.find_subject_folders(path_to_data_set)]

    def find_subject_folders(self, path_to_data_set):
        return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))


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
        return os.path.basename(path_to_subject).lstrip("sub-")


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


class GroupReader(object):
    def load_group(self, path_to_group_folder):
        group_name = self.parse_group_name(path_to_group_folder)
        images = self.read_images(path_to_group_folder)
        if group_name == "func":
            return FunctionalGroup(name=group_name, images=images, path=path_to_group_folder)
        else:
            return Group(name=group_name, images=images, path=path_to_group_folder)

    def parse_group_name(self, path_to_group_folder):
        return os.path.basename(path_to_group_folder)

    def read_images(self, path_to_group_folder):
        return [read_image(image_file) for image_file in glob.glob(os.path.join(path_to_group_folder, "*.nii*"))]


class ImageReader(object):
    def read_image(self, path_to_image):
        modality = self.parse_image_modality(path_to_image)
        if modality == "bold":
            return FunctionalImage(modality=modality,
                                   file_path=path_to_image,
                                   task_name=self.parse_task_name(path_to_image))
        else:
            return Image(modality=modality, file_path=path_to_image)

    def parse_image_modality(self, path_to_image):
        return os.path.basename(path_to_image).split(".")[0].split("_")[-1]

    def parse_task_name(self, path_to_image):
        return re.search('(?<=task-)[a-z]*', os.path.basename(path_to_image)).group(0)


def read_subject(path_to_subject_folder):
    return SubjectReader().read_subject(path_to_subject_folder)


def read_group(path_to_group_folder):
    return GroupReader().load_group(path_to_group_folder)


def read_session(path_to_session_folder):
    return SessionReader().read_session(path_to_session_folder)


def read_image(path_to_image_file):
    return ImageReader().read_image(path_to_image_file)
