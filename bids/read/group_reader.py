import glob
import os

from bids.base.group import FunctionalGroup, Group
from bids.read.image_reader import read_image


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


def read_group(path_to_group_folder):
    return GroupReader().load_group(path_to_group_folder)