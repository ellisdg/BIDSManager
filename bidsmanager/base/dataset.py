import sqlite3
from collections import OrderedDict

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
    _sql_config = {"Session": {"columns": {"name": "TEXT",
                                           "id": "INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE"},
                               "foreign_keys": {"subject_id": "Subject(id)"}},
                   "Subject": {"columns": {"id": "CHAR(2)"}}}

    def __init__(self, bids_dataset, path):
        self.enforce_foreign_keys()
        self.dataset = bids_dataset
        self.connection = connect_to_database(path)
        self.cursor = self.connection.cursor()
        self.write_database()

    def enforce_foreign_keys(self):
        for column_specifications in self._sql_config.values():
            column_specifications["columns"] = OrderedDict(column_specifications["columns"])
            if "foreign_keys" in column_specifications:
                for foreign_key, sql_reference in column_specifications["foreign_keys"].items():
                    column_specifications["columns"][foreign_key] = self.get_column_config(sql_reference)
                    column_specifications["columns"]["FOREIGN KEY({0})".format(foreign_key)] = "REFERENCES {0}".format(
                        sql_reference)

    def get_column_config(self, sql_reference):
        table_name, column_name = sql_reference.rstrip(")").split("(")
        return self._sql_config[table_name]["columns"][column_name]

    def write_database(self):
        self.write_info_to_database()
        self.connection.commit()

    def write_info_to_database(self):
        self.write_bids_tables()
        for subject in self.dataset.get_subjects():
            self.insert_subject_into_database(subject)

    def insert_subject_into_database(self, subject):
        self.insert_into_database("Subject", "(id)", "('{0}')".format(subject.get_id()))
        for session in subject.get_sessions():
            self.insert_session_into_database(session)

    def insert_session_into_database(self, session):
        if session.get_name():
            session_id = self.insert_into_database("Session", "(name, subject_id)", "('{0}', '{1}')".format(
                session.get_name(), session.get_parent().get_id()))
        else:
            session_id = -1
        for image in session.get_images():
            self.insert_image_into_database(image, session_id)

    def insert_image_into_database(self, image, session_id):
        try:
            task_name = image.get_task_name()
        except AttributeError:
            task_name = ""
        self.insert_into_database("Image", "(modality, session_id, taskname)",
                                  "('{0}', '{1}', '{2}')".format(image.get_modality(), session_id, task_name))

    def write_bids_tables(self):
        self.create_table_from_config("Subject")
        self.create_table_from_config("Session")
        self.create_table("Image", "(modality TEXT, session_id INTEGER, taskname TEXT)")

    def insert_into_database(self, table_name, columns, values):
        execute_statement(self.cursor, "INSERT INTO {table} {columns} VALUES {values};".format(table=table_name,
                                                                                               columns=columns,
                                                                                               values=values))
        return self.cursor.lastrowid

    def create_table(self, table_name, columns, drop_table=True):
        if drop_table:
            self.drop_table(table_name)
        execute_statement(self.cursor, "CREATE TABLE {0} {1}".format(table_name, columns))

    def create_table_from_config(self, table_name):
        self.create_table(table_name, format_columns_specifications(self._sql_config[table_name]["columns"]))

    def drop_table(self, name):
        execute_statement(self.cursor, "DROP TABLE IF EXISTS {0};".format(name))

    def __del__(self):
        self.connection.commit()
        self.connection.close()


def connect_to_database(sql_file):
    return sqlite3.connect(sql_file)


def execute_statement(cursor, sql_statement):
    return cursor.execute(sql_statement)


def format_columns_specifications(specifications):
    return "({0})".format(", ".join([" ".join((column, spec)) for column, spec in specifications.items()]))
