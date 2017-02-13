import glob
import os

from ..base.group import FunctionalGroup, Group
from ..read.image_reader import read_image


class GroupReader(object):
    def load_group_from_bids_path(self, path_to_group_folder):
        group_name = self.parse_group_name(path_to_group_folder)
        images = self.read_images(path_to_group_folder)
        return self.load_group(path_to_group_folder=path_to_group_folder, group_name=group_name, images=images)

    @staticmethod
    def load_group(path_to_group_folder=None, group_name=None, images=None):
        if group_name == "func":
            return FunctionalGroup(name=group_name, images=images, path=path_to_group_folder)
        else:
            return Group(name=group_name, images=images, path=path_to_group_folder)

    @staticmethod
    def parse_group_name(path_to_group_folder):
        return os.path.basename(path_to_group_folder)

    @staticmethod
    def read_images(path_to_group_folder):
        return [read_image(image_file) for image_file in glob.glob(os.path.join(path_to_group_folder, "*.nii*"))]


def read_group(path_to_group_folder):
    return GroupReader().load_group_from_bids_path(path_to_group_folder)
