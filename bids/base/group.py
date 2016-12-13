

class Group(object):
    def __init__(self):
        self._images = []

    def add_image(self, image):
        self._images.append(image)

    def list_image_paths(self):
        image_paths = []
        for image in self._images:
            image_paths.append(image.get_file_path())
        return image_paths
