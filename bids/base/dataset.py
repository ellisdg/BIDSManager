from base import BIDSFolder


class DataSet(BIDSFolder):
    def __init__(self, subjects=None, *inputs, **kwargs):
        super(DataSet, self).__init__(*inputs, **kwargs)
        self.subjects = self._dict
        self._folder_type = "dataset"
        if subjects:
            self.add_subjects(subjects)

    def add_subjects(self, subjects):
        for subject in subjects:
            self.add_subject(subject)

    def add_subject(self, subject):
        self._add_object(subject, subject.get_id(), "subject")

    def get_subject_ids(self):
        return sorted([subject_id for subject_id in self.subjects])

    def get_number_of_subjects(self):
        return len(self.subjects)

    def get_subject(self, subject_id):
        return self.subjects[subject_id]

    def get_subjects(self):
        return self.subjects.values()

    def get_image_paths(self, modality=None, acquisition=None):
        image_paths = []
        for subject in self.subjects.itervalues():
            image_paths.extend(subject.get_image_paths(modality=modality, acquisition=acquisition))
        return image_paths

    def has_subject_id(self, subject_id):
        return subject_id in self.get_subject_ids()

