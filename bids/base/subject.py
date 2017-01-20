from base import BIDSFolder


class Subject(BIDSFolder):
    def __init__(self, subject_id=None, *inputs, **kwargs):
        super(Subject, self).__init__(*inputs, **kwargs)
        self.subject_id = subject_id
        self._sessions = self._dict
        self._folder_type = "subject"

    def add_session(self, session):
        self._add_object(session, session.get_name(), "session")

    def get_basename(self):
        return "sub-{0}".format(self.get_id())

    def get_id(self):
        return self.subject_id

    def get_session(self, session_name):
        return self._sessions[session_name]

    def get_sessions(self):
        return self._sessions.values()

    def get_image_paths(self, group_name=None, modality=None, acquisition=None):
        image_paths = []
        for session in self._sessions.itervalues():
            image_paths.extend(session.get_image_paths(group_name=group_name, modality=modality,
                                                       acquisition=acquisition))
        return image_paths

    def get_task_names(self):
        return self._sessions.values()[0].get_group("func").get_task_names()

    def get_session_names(self):
        return self._sessions.keys()

    def has_session(self, session_name):
        return session_name in self._sessions
