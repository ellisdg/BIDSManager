import os

from bidsmanager.utils.session_utils import modality_to_group_name
from .base import BIDSFolder
from .group import FunctionalGroup
from ..utils.session_utils import load_group


class Session(BIDSFolder):
    def __init__(self, name=None, groups=None, *inputs, **kwargs):
        super(Session, self).__init__(*inputs, **kwargs)
        self._groups = self._dict
        self._name = name
        self._type = "Session"
        if groups:
            self.add_groups(groups)

    def add_group(self, group):
        self._add_object(group, group.get_name(), "Group")

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

    def get_images(self, group_name=None, modality=None, acquisition=None, run_number=None, task_name=None):
        images = []
        for group in self._groups.values():
            if not group_name or group_name == group.get_name():
                if isinstance(group, FunctionalGroup):
                    images.extend(group.get_images(modality=modality, acquisition=acquisition, run_number=run_number,
                                                   task_name=task_name))
                elif not task_name:
                    images.extend(group.get_images(modality=modality, acquisition=acquisition, run_number=run_number))
        return images

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

    def update(self, run=False, move=False):
        super(Session, self).update(run=run, move=move)
        tsv_basename = "_".join([self.get_parent().get_basename(), self.get_basename(), "scans.tsv"])
        self.write_child_metadata(tsv_basename=tsv_basename)

    def compile_child_metadata(self):
        metadata = dict()
        for image in self.get_images():
            if image.get_tsv_metadata():
                metadata[os.path.join(image.get_group().get_name(), image.get_basename())] = image.get_tsv_metadata()
        return metadata
