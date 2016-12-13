

class Session(object):
    def __init__(self):
        self._groups = []

    def add_group(self, group):
        self._groups.append(group)

    def list_image_paths(self):
        image_paths = []
        for group in self._groups:
            image_paths.extend(group.list_image_paths())
        return image_paths
