from bids.utils.session_utils import modality_to_group_name
from .base import BIDSFolder
from ..utils.session_utils import load_group


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

    def add_image(self, image):
        group_name = modality_to_group_name(image.get_modality())
        try:
            group = self.get_group(group_name)
        except KeyError:
            group = load_group(group_name=group_name)
            self.add_group(group)
        group.add_image(image)

    def get_basename(self):
        return "ses-{0}".format(self.get_name())

    def get_image_paths(self, group_name=None, modality=None, acquisition=None, run=None):
        image_paths = []
        for group in self._groups.values():
            if (group_name and group_name == group.get_name()) or not group_name:
                image_paths.extend(group.get_image_paths(modality=modality, acquisition=acquisition, run_number=run))
        return image_paths

    def get_group(self, group_name):
        return self._groups[group_name]

    def get_groups(self):
        return list(self._groups.values())

    def get_group_names(self):
        return self._groups.keys()

    def get_name(self):
        return self._name

    def has_group(self, group_name):
        return group_name in self._groups
