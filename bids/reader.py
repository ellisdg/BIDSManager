from base.dataset import DataSet
from base.subject import Subject
from base.image import Image
from base.group import Group
from base.session import Session
import glob
import os


class Reader(object):
    def __init__(self):
        super(Reader, self).__init__()

    def load_data_set(self, path_to_data_set):
        return DataSet(self.get_subject_ids(path_to_data_set))

    def get_subject_ids(self, path_to_data_set):
        return [self.load_subject(path_to_subject) for path_to_subject in self.find_subject_folders(path_to_data_set)]

    def find_subject_folders(self, path_to_data_set):
        return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))

    def load_subject(self, path_to_subject):
        subject = Subject(os.path.basename(path_to_subject).lstrip("sub-"))
        session = Session()
        for group in self.load_groups(path_to_subject):
            session.add_group(group)
        subject.add_session(session)
        return subject

    def load_groups(self, path_to_folder):
        return [self.load_group(group_folder) for group_folder in glob.glob(os.path.join(path_to_folder, "*"))]

    def load_group(self, path_to_group_folder):
        group = Group()
        for image_file in glob.glob(os.path.join(path_to_group_folder, "*.nii*")):
            group.add_image(Image(image_file))
        return group

