from image import FunctionalImage
from base import BIDSFolder


class Group(BIDSFolder):
    def __init__(self, name=None, images=None, *inputs, **kwargs):
        super(Group, self).__init__(*inputs, **kwargs)
        self._images = self._dict
        self._folder_type = "group"
        if images:
            self.add_images(images)
        self._name = name

    def add_image(self, image):
        self._add_object(image, image.get_image_key(), "image")

    def add_images(self, images):
        for image in images:
            self.add_image(image)

    def get_name(self):
        return self._name

    def get_basename(self):
        return self.get_name()

    def get_image_paths(self, modality=None, acquisition=None):
        image_paths = []
        for image in self._images.itervalues():
            if not (modality and modality != image.get_modality()) \
                    and not (acquisition and acquisition != image.get_acquisition()):
                image_paths.append(image.get_path())
        return image_paths

    def get_modalities(self):
        return [image.get_modality() for image in self._images.itervalues()]

    def get_images(self):
        return self._images.values()


class FunctionalGroup(Group):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalGroup, self).__init__(*inputs, **kwargs)

    def add_image(self, image):
        if isinstance(image, FunctionalImage):
            super(FunctionalGroup, self).add_image(image)
        else:
            raise TypeError("Cannot add non-functional image to a functional group")

    def get_task_names(self):
        return [image.get_task_name() for image in self._images.itervalues()]
