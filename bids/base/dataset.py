

class DataSet(object):
    def __init__(self, subjects=None):
        self.subjects = []
        if subjects:
            for subject in subjects:
                self.add_subject(subject)

    def add_subject(self, subject):
        if subject.get_id() not in self.list_subject_ids():
            self.subjects.append(subject)
        else:
            raise(ValueError("Duplicate subject subject_id found."))

    def list_subject_ids(self):
        return [subject.get_id() for subject in self.subjects]

    def get_number_of_subjects(self):
        return len(self.subjects)
