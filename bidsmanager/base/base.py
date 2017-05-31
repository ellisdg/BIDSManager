import os
import abc

from ..write.dataset_writer import write_tsv


class BIDSObject(object):
    def __init__(self, path=None, parent=None, metadata=None):
        self._parent = None
        self.set_parent(parent)
        self._previous_path = None
        if metadata is None:
            self._metadata = dict()
        else:
            self._metadata = metadata
        if path:
            self._path = os.path.abspath(path)
        else:
            self._path = path
        self._name = None
        self._type = "BIDSObject"

    def get_parent(self):
        return self._parent

    def get_path(self):
        return os.path.abspath(self._path)

    def set_path(self, path):
        if self._path and os.path.exists(self._path):
            self._previous_path = self._path
        self._path = os.path.abspath(path)

    def get_basename(self):
        if self._path:
            return os.path.basename(self._path)

    def set_parent(self, parent):
        self._parent = parent

    def set_name(self, name):
        if self._parent:
            self._parent.modify_key(self._name, name)
        self._name = name

    def get_metadata(self, key=None):
        if key:
            return self._metadata[key]
        return self._metadata

    def add_metadata(self, key, data):
        self._metadata[key] = data

    def get_bids_type(self):
        return self._type


class BIDSFolder(BIDSObject):
    def __init__(self, input_dict=None, *inputs, **kwargs):
        if input_dict:
            self._dict = input_dict
        else:
            self._dict = dict()
        super(BIDSFolder, self).__init__(*inputs, **kwargs)
        self._type = "BIDSFolder"

    def _add_object(self, object_to_add, object_name, object_title):
        if object_name not in self._dict:
            self._dict[object_name] = object_to_add
            object_to_add.set_parent(self)
        else:
            raise(KeyError("Duplicate {0} found in {1}: {2}".format(object_title, self._type, object_name)))

    def modify_key(self, key, new_key):
        self._add_object(self._dict.pop(key), new_key, "object")

    def get_children(self):
        return self._dict.values()

    def get_image_paths(self, **kwargs):
        return [image.get_path() for image in self.get_images(**kwargs)]

    def set_parent(self, parent):
        super(BIDSFolder, self).set_parent(parent)
        self.update_parent_of_children()

    def update_parent_of_children(self):
        for child in self.get_children():
            child.set_parent(self)

    def update(self, move=False):
        if self.get_path() and not os.path.exists(self.get_path()):
            os.makedirs(self.get_path())

        for child in self._dict.values():
            basename = child.get_basename()
            if basename:
                child.set_path(os.path.join(self.get_path(), basename))
                child.update(move=move)

        if self._previous_path and not os.listdir(self._previous_path):
            os.rmdir(self._previous_path)

    def write_child_metadata(self, tsv_basename):
        metadata = self.compile_child_metadata()
        if metadata:
            write_tsv(metadata, os.path.join(self.get_path(), tsv_basename))

    def compile_child_metadata(self):
        metadata = dict()
        for child in self.get_children():
            if child.get_metadata():
                metadata[child.get_basename()] = child.get_metadata()
        return metadata
