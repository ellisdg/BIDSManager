from .image import FunctionalImage
from .base import BIDSFolder


class Group(BIDSFolder):
    def __init__(self, name=None, images=None, *inputs, **kwargs):
        self._flags = dict()
        super(Group, self).__init__(*inputs, **kwargs)
        self._images = self._dict
        self._folder_type = "group"
        if images:
            self.add_images(images)
        self._name = name

    def add_image(self, image):
        image_key = image.get_image_key()
        if image_key in self._flags:
            self._flags[image_key] += 1
            image._run_number = self._flags[image_key]
            image_key = image.get_image_key()
        try:
            self._add_object(image, image_key, "image")
        except KeyError:
            self._flags[image_key] = 0
            self.add_images([self._images.pop(image_key), image])

    def add_images(self, images):
        for image in images:
            self.add_image(image)

    def get_name(self):
        return self._name

    def get_basename(self):
        return self.get_name()

    def get_image_paths(self, modality=None, acquisition=None, run_number=None):
        image_paths = []
        for image in self._images.values():
            if not (modality and modality != image.get_modality()) \
                    and not (acquisition and acquisition != image.get_acquisition())\
                    and not (run_number and run_number != image.get_run_number()):
                image_paths.append(image.get_path())
        return image_paths

    def get_modalities(self):
        return [image.get_modality() for image in self._images.values()]

    def get_images(self):
        return list(self._images.values())


class FunctionalGroup(Group):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalGroup, self).__init__(*inputs, **kwargs)

    def add_image(self, image):
        if isinstance(image, FunctionalImage):
            super(FunctionalGroup, self).add_image(image)
        else:
            raise TypeError("Cannot add non-functional image to a functional group")

    def get_task_names(self):
        return [image.get_task_name() for image in self._images.values()]
