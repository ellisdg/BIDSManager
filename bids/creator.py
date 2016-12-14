from base.image import FunctionalImage, Image
from base.group import FunctionalGroup, Group


class GroupCreator(object):
    def __init__(self, group_name):
        self.group_name = group_name
        self._group = self.create_group()

    def create_group(self):
        if self.group_name == "func":
            return FunctionalGroup()
        else:
            return Group(self.group_name)

    def add_image(self, image):
        if isinstance(self._group, FunctionalGroup) and not isinstance(image, FunctionalImage):
            self._group.add_image(FunctionalImage(image.get_file_path()))
        else:
            self._group.add_image(image)

    def get_group(self):
        return self._group
