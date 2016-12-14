

class Session(object):
    def __init__(self):
        self._groups = []

    def add_group(self, group):
        self._groups.append(group)

    def list_image_paths(self, group_name=None):
        image_paths = []
        for group in self._groups:
            if (group_name and group_name == group.get_name()) or not group_name:
                image_paths.extend(group.list_image_paths())
        return image_paths

    def get_group(self, group_name):
        for group in self._groups:
            if group.get_name() == group_name:
                return group
