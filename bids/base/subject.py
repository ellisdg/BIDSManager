

class Subject(object):
    def __init__(self, subject_id=None):
        self.subject_id = subject_id
        self.sessions = []

    def add_session(self, session):
        self.sessions.append(session)

    def get_id(self):
        return self.subject_id
