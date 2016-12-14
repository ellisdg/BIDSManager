

class Subject(object):
    def __init__(self, subject_id=None):
        self.subject_id = subject_id
        self.sessions = []

    def add_session(self, session):
        self.sessions.append(session)

    def get_id(self):
        return self.subject_id

    def list_image_paths(self, group_name=None):
        return self.sessions[0].list_image_paths(group_name=group_name)

    def list_task_names(self):
        return self.sessions[0].get_group("func").get_task_names()

    def list_sessions(self):
        return [session.get_name() for session in self.sessions]
