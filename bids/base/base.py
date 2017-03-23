import os
import abc


class BIDSObject(object):
    def __init__(self, path=None, parent=None):
        self._parent = None
        self.set_parent(parent)
        self._previous_path = None
        if path:
            self._path = os.path.abspath(path)
        else:
            self._path = path
        self._name = None

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


class BIDSFolder(BIDSObject):
    __metaclass__ = abc.ABCMeta

    def __init__(self, input_dict=None, *inputs, **kwargs):
        super(BIDSFolder, self).__init__(*inputs, **kwargs)
        if input_dict:
            self._dict = input_dict
        else:
            self._dict = dict()
        self._folder_type = "BIDSFolder"

    def _add_object(self, object_to_add, object_name, object_title):
        if object_name not in self._dict:
            self._dict[object_name] = object_to_add
            object_to_add.set_parent(self)
        else:
            raise(KeyError("Duplicate {0} found in {1}: {2}".format(object_title, self._folder_type, object_name)))

    def modify_key(self, key, new_key):
        self._dict[new_key] = self._dict.pop(key)

    def get_image_paths(self, **kwargs):
        return [image.get_path() for image in self.get_images(**kwargs)]

    @abc.abstractmethod
    def get_images(self, **kwargs):
        return []

    def update(self, run=False, move=False):
        if run:
            if self._path and not os.path.exists(self._path):
                os.makedirs(self._path)

            for child in self._dict.values():
                if isinstance(child, BIDSObject):
                    basename = child.get_basename()
                else:
                    basename = None
                if basename:
                    child.set_path(os.path.join(self._path, basename))
                    child.update(run=True, move=move)

            if self._previous_path and not os.listdir(self._previous_path):
                os.rmdir(self._previous_path)
        else:
            print("Warning: Updating will possibly move and possibly delete parts of the dataset!")
            print("    To update, set run=True.")
