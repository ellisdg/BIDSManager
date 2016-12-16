from image import FunctionalImage


class Group(object):
    def __init__(self, name=None, images=None):
        if images:
            self._images = images
        else:
            self._images = []
        self._name = name

    def add_image(self, image):
        self._images.append(image)

    def get_name(self):
        return self._name

    def get_image_paths(self):
        image_paths = []
        for image in self._images:
            image_paths.append(image.get_file_path())
        return image_paths

    def get_modalities(self):
        return [image.get_modality() for image in self._images]


class FunctionalGroup(Group):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalGroup, self).__init__(*inputs, **kwargs)

    def add_image(self, image):
        if isinstance(image, FunctionalImage):
            super(FunctionalGroup, self).add_image(image)
        else:
            raise TypeError("Cannot add non-functional image to a functional group")

    def get_task_names(self):
        return [image.get_task_name() for image in self._images]
