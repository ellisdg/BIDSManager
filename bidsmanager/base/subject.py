from .base import BIDSFolder


class Subject(BIDSFolder):
    def __init__(self, subject_id=None, *inputs, **kwargs):
        super(Subject, self).__init__(*inputs, **kwargs)
        self.set_name(subject_id)
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

    def get_images(self, group_name=None, modality=None, acquisition=None, run_number=None, session_name=None,
                   task_name=None):
        if session_name:
            return self.get_session(session_name).get_images(group_name=group_name, modality=modality,
                                                             acquisition=acquisition, run_number=run_number,
                                                             task_name=task_name)
        else:
            images = []
            for bids_session in self._sessions.values():
                images.extend(bids_session.get_images(group_name=group_name, modality=modality, acquisition=acquisition,
                                                      run_number=run_number, task_name=task_name))
            return images

    def get_task_names(self):
        return self.get_sessions()[0].get_group("func").get_task_names()

    def get_session_names(self):
        return self._sessions.keys()

    def has_session(self, session_name):
        return session_name in self._sessions
