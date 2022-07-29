from .base import BIDSFolder


class Subject(BIDSFolder):
    def __init__(self, *inputs, **kwargs):
        super(Subject, self).__init__(*inputs, **kwargs)
        self._sessions = self._dict
        self._type = "Subject"

    def add_session(self, session):
        self._add_object(session, session.get_name(), "Session")

    def get_basename(self):
        return "sub-{0}".format(self.get_id())

    def get_id(self):
        return self._name

    def get_session(self, session_name):
        return self._sessions[session_name]

    def get_sessions(self):
        return list(self._sessions.values())

    def get_images(self, group_name=None, session_name=None, **kwargs):
        if session_name:
            return self.get_session(session_name).get_images(group_name=group_name, **kwargs)
        else:
            images = []
            for bids_session in self._sessions.values():
                images.extend(bids_session.get_images(group_name=group_name, **kwargs))
            return images

    def get_task_names(self):
        return self.get_sessions()[0].get_group("func").get_task_names()

    def get_session_names(self):
        return self._sessions.keys()

    def has_session(self, session_name):
        return session_name in self._sessions

    def update(self, move=False):
        super(Subject, self).update(move=move)
        tsv_basename = "_".join([self.get_basename(), "sessions.tsv"])
        self.write_child_metadata(tsv_basename)
