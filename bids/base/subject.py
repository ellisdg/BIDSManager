

class Subject(object):
    def __init__(self, subject_id=None):
        self.subject_id = subject_id
        self.sessions = dict()

    def add_session(self, session):
        name = session.get_name()
        self.sessions[name] = session

    def get_id(self):
        return self.subject_id

    def get_session(self, session_name):
        return self.sessions[session_name]

    def get_sessions(self):
        return self.sessions.values()

    def get_image_paths(self, group_name=None):
        return self.sessions.values()[0].get_image_paths(group_name=group_name)

    def get_task_names(self):
        return self.sessions.values()[0].get_group("func").get_task_names()

    def get_session_names(self):
        return self.sessions.keys()
