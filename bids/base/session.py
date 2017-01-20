from base import BIDSFolder


class Session(BIDSFolder):
    def __init__(self, name=None, groups=None, *inputs, **kwargs):
        super(Session, self).__init__(*inputs, **kwargs)
        self._groups = self._dict
        self._name = name
        self._folder_type = "session"
        if groups:
            self.add_groups(groups)

    def add_group(self, group):
        self._add_object(group, group.get_name(), "group")

    def add_groups(self, groups):
        [self.add_group(group) for group in groups]

    def get_image_paths(self, group_name=None, modality=None, acquisition=None):
        image_paths = []
        for group in self._groups.itervalues():
            if (group_name and group_name == group.get_name()) or not group_name:
                image_paths.extend(group.get_image_paths(modality=modality, acquisition=acquisition))
        return image_paths

    def get_group(self, group_name):
        return self._groups[group_name]

    def get_groups(self):
        return self._groups.values()

    def get_group_names(self):
        return self._groups.keys()

    def get_name(self):
        return self._name

    def has_group(self, group_name):
        return group_name in self._groups
