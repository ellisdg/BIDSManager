from base import BIDSObject


class Session(BIDSObject):
    def __init__(self, name=None, *inputs, **kwargs):
        super(Session, self).__init__(*inputs, **kwargs)
        self._groups = []
        self._name = name

    def add_group(self, group):
        self._groups.append(group)

    def get_image_paths(self, group_name=None, modality=None):
        image_paths = []
        for group in self._groups:
            if (group_name and group_name == group.get_name()) or not group_name:
                image_paths.extend(group.get_image_paths(modality=modality))
        return image_paths

    def get_group(self, group_name):
        for group in self._groups:
            if group.get_name() == group_name:
                return group

    def get_groups(self):
        return self._groups

    def get_group_names(self):
        return [group.get_name() for group in self._groups]

    def get_name(self):
        return self._name
