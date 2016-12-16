from base.image import FunctionalImage, Image
from base.group import FunctionalGroup, Group


class GroupCreator(object):
    def create_group(self, group_name, images):
        if group_name == "func":
            return self.create_functional_group(images)
        else:
            return self.add_images(images, Group(group_name))

    def create_functional_group(self, images):
        return self.add_images([FunctionalImage(image.get_file_path()) for image in images],
                               FunctionalGroup())

    def add_images(self, images, group):
        for image in images:
            group.add_image(image)
        return group

    def add_image(self, image):
        self._group.add_image(image)

    def get_group(self):
        return self._group
