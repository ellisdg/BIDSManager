import sqlite3

from .base import BIDSFolder


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
        return list(self.subjects.values())

    def get_images(self, modality=None, acquisition=None, subject_id=None, session=None, run_number=None,
                   group_name=None, task_name=None):
        if subject_id:
            return self.get_subject(subject_id=subject_id).get_images(modality=modality, acquisition=acquisition,
                                                                      session_name=session, run_number=run_number,
                                                                      group_name=group_name, task_name=task_name)
        else:
            images = []
            for bids_subject in self.subjects.values():
                images.extend(bids_subject.get_images(modality=modality, acquisition=acquisition, session_name=session,
                                                      run_number=run_number, group_name=group_name,
                                                      task_name=task_name))
            return images

    def has_subject_id(self, subject_id):
        return subject_id in self.get_subject_ids()

    def create_sql_interface(self, sql_file):
        return SQLInterface(self, sql_file)


class SQLInterface(object):
    def __init__(self, bids_dataset, path):
        self.dataset = bids_dataset
        self.connection = connect_to_database(path)
        self.write_database()

    def write_database(self):
        self.create_image_table()
        self.write_subjects_to_database()
        self.connection.commit()

    def write_subjects_to_database(self):
        table_name = "Subject"
        self.drop_table(table_name)
        execute_statement(self.connection, "CREATE TABLE {0} (id CHAR(2));".format(table_name))
        session_table_name = "Session"
        self.drop_table(session_table_name)
        execute_statement(self.connection,
                          "CREATE TABLE {0} (id TEXT)".format(session_table_name))
        for subject in self.dataset.get_subjects():
            execute_statement(self.connection, "INSERT INTO {0} (id) VALUES ('{1}');".format(table_name,
                                                                                             subject.get_id()))
            for session in subject.get_sessions():
                session_name = session.get_name()
                if session_name:
                    execute_statement(self.connection,
                                      "INSERT INTO {0} (id) VALUES ('{1}');".format(session_table_name,
                                                                                    session_name))

    def create_image_table(self):
        table_name = "Image"
        self.drop_table(table_name)
        execute_statement(self.connection,
                          "CREATE TABLE {0} (modality TEXT, subject CHAR(2), taskname TEXT)".format(table_name))
        for image in self.dataset.get_images():
            try:
                taskname = image.get_task_name()
            except AttributeError:
                taskname = ""

            execute_statement(self.connection,
                              """INSERT INTO {0} (modality, subject, taskname)
                                 VALUES ('{1}', '{2}', '{3}');""".format(table_name, image.get_modality(),
                                                                         image.get_subject().get_id(), taskname))

    def drop_table(self, name):
        execute_statement(self.connection, "DROP TABLE IF EXISTS {0};".format(name))

    def __del__(self):
        self.connection.commit()
        self.connection.close()


def connect_to_database(sql_file):
    return sqlite3.connect(sql_file)


def execute_statement(connection, sql_statement):
    return connection.cursor().execute(sql_statement)