import os


class BIDSObject(object):
    def __init__(self, path=None):
        if path:
            self._path = os.path.abspath(path)
        else:
            self._path = path

    def get_path(self):
        return self._path
