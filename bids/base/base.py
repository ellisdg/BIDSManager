import os


class BIDSObject(object):
    def __init__(self, path=None, parent=None):
        self._parent = None
        self.set_parent(parent)
        self._previous_path = None
        if path:
            self._path = os.path.abspath(path)
        else:
            self._path = path

    def get_parent(self):
        return self._parent

    def get_path(self):
        return self._path

    def set_path(self, path):
        if self._path and os.path.exists(self._path):
            self._previous_path = self._path
        self._path = os.path.abspath(path)

    def get_basename(self):
        if self._path:
            return os.path.basename(self._path)

    def set_parent(self, parent):
        self._parent = parent


class BIDSFolder(BIDSObject):
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
            raise(ValueError("Duplicate {0} found in {1}: {2}".format(object_title, self._folder_type, object_name)))

    def update(self, run=False):
        if run:
            if self._path and not os.path.exists(self._path):
                os.makedirs(self._path)

            for child in self._dict.itervalues():
                if isinstance(child, BIDSObject):
                    basename = child.get_basename()
                else:
                    basename = None
                if basename:
                    child.set_path(os.path.join(self._path, basename))
                    child.update(run=True)

            if self._previous_path and not os.listdir(self._previous_path):
                os.rmdir(self._previous_path)
        else:
            print("Warning: Updating will possibly move and possibly delete parts of the dataset!")
            print("    To update, set run=True.")
