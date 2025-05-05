from .base import BIDSFolder


class Group(BIDSFolder):
    def __init__(self, *inputs, images=None, **kwargs):
        self._flags = dict()
        super(Group, self).__init__(*inputs, **kwargs)
        self._images = self._dict
        self._type = "Group"
        if images:
            self.add_images(images)

    def add_image(self, image):
        image_key = image.get_image_key()
        if image_key in self._flags:
            self._flags[image_key] += 1
            image._run = self._flags[image_key]
            image_key = image.get_image_key()
        try:
            self._add_object(image, image_key, "Image")
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

    def get_images(self, **kwargs):
        images = []
        for image in self._images.values():
            if image.is_match(**kwargs):
                images.append(image)
        return images

    def get_modalities(self):
        return [image.get_modality() for image in self._images.values()]

    def get_all_images(self):
        return list(self._images.values())


class FunctionalGroup(Group):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalGroup, self).__init__(*inputs, **kwargs)

    def get_task_names(self):
        return [image.get_task_name() for image in self._images.values()]
