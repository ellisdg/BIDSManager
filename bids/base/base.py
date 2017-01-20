import os


class BIDSObject(object):
    def __init__(self, path=None):
        if path:
            self._path = os.path.abspath(path)
        else:
            self._path = path

    def get_path(self):
        return self._path


class BIDSFolder(BIDSObject):
    def __init__(self, input_dict=None, *inputs, **kwargs):
        super(BIDSFolder, self).__init__(*inputs, **kwargs)
        if input_dict:
            self._dict = input_dict
        else:
            self._dict = dict()
        self._folder_type = "BIDSFolder"

    def _add_object(self, object_to_add, object_name, object_title):
        if not self._dict.has_key(object_name):
            self._dict[object_name] = object_to_add
        else:
            raise(ValueError("Duplicate {0} found in {1}: {2}".format(object_title, self._folder_type, object_name)))
