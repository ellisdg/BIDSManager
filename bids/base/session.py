

class Session(object):
    def __init__(self):
        self._groups = []

    def add_group(self, group):
        self._groups.append(group)
