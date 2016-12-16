

class DataSet(object):
    def __init__(self, subjects=None):
        self.subjects = dict()
        if subjects:
            for subject in subjects:
                self.add_subject(subject)

    def add_subject(self, subject):
        if subject.get_id() not in self.get_subject_ids():
            self.subjects[subject.get_id()] = subject
        else:
            raise(ValueError("Duplicate subject subject_id found."))

    def get_subject_ids(self):
        return sorted([subject_id for subject_id in self.subjects])

    def get_number_of_subjects(self):
        return len(self.subjects)

    def get_subject(self, subject_id):
        return self.subjects[subject_id]

    def get_subjects(self):
        return self.subjects.values()
