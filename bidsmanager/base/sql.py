import copy
import sqlite3
from collections import OrderedDict

from bidsmanager.base.base import BIDSFolder


class SQLInterface(object):
    _sql_config = {"Session": {"columns": {"name": "TEXT",
                                           "id": "INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE"},
                               "foreign_keys": {"subject_id": "Subject(id)"}},
                   "Subject": {"columns": {"name": "TEXT",
                                           "id": "INTEGER NOT NULL PRIMARY KEY UNIQUE"}},
                   "Image": {"columns": {"id": "INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE",
                                         "modality": "TEXT",
                                         "task_name": "TEXT",
                                         "path": "TEXT",
                                         "group_name": "TEXT",
                                         "acquisition": "TEXT"},
                             "foreign_keys": {"session_id": "Session(id)"}}}

    def __init__(self, bids_dataset, path):
        self._sql_config = copy.deepcopy(self._sql_config)
        self.recursive_config_edit([bids_dataset])
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
                    column_specifications["columns"][foreign_key] = self.get_column_config(sql_reference).split(" ")[0]
                    column_specifications["columns"]["FOREIGN KEY({0})".format(foreign_key)] = "REFERENCES {0}".format(
                        sql_reference)

    def add_metadata_to_config(self, keys, table_name):
        if table_name not in self._sql_config:
            self._sql_config[table_name] = {"columns": OrderedDict()}
        for key in keys:
            self._sql_config[table_name]["columns"][key] = "TEXT"

    def recursive_config_edit(self, bids_objects):
        for bids_object in bids_objects:
            if isinstance(bids_object, BIDSFolder):
                self.recursive_config_edit(bids_object.get_children())
        keys, table_name = get_set_of_metadata_keys_and_types(bids_objects)
        if keys and table_name != "Group":
            self.add_metadata_to_config(keys, table_name.pop())

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
        self.insert_dict_into_database("Subject", {"name": subject.get_id(), "id": int(subject.get_id())})
        for session in subject.get_sessions():
            self.insert_session_into_database(session)

    def insert_session_into_database(self, session):
        if session.get_name():
            session_id = self.insert_dict_into_database("Session",
                                                        {"name": session.get_name(),
                                                         "subject_id": session.get_parent().get_id()})
        else:
            session_id = -1
        for image in session.get_images():
            self.insert_image_into_database(image, session_id)

    def insert_image_into_database(self, image, session_id):
        try:
            task_name = image.get_task_name()
        except AttributeError:
            task_name = ""
        data = {"session_id": session_id,
                "modality": image.get_modality(),
                "task_name": task_name,
                "path": image.get_path(),
                "group_name": image.get_group().get_name(),
                "acquisition": image.get_acquisition() if image.get_acquisition() else ""}
        for key, value in image.get_metadata().items():
            data[str(key)] = str(value)
        self.insert_dict_into_database("Image", data)

    def write_bids_tables(self):
        for table_name in self._sql_config:
            self.create_table_from_config(table_name)

    def insert_dict_into_database(self, table_name, dictionary):
        keys = dictionary.keys()
        values = dictionary.values()
        if len(keys) == 1:
            value = values[0]
            if isinstance(value, str):
                value = "'{0}'".format(value)
            keys = "({0})".format(keys[0])
            values = "({0})".format(value)
        else:
            keys = str(tuple(keys))
            values = str(tuple(values))
        return self.insert_into_database(table_name, keys, values)

    def insert_into_database(self, table_name, columns, values):
        execute_statement(self.cursor, "INSERT INTO {table} {columns} VALUES {values};".format(table=table_name,
                                                                                               columns=columns,
                                                                                               values=values))
        return self.cursor.lastrowid

    def create_table(self, table_name, columns, drop_table=True):
        if drop_table:
            self.drop_table(table_name)
        execute_statement(self.cursor, "CREATE TABLE {0} {1};".format(table_name, columns))

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


def get_set_of_metadata_keys_and_types(bids_objects):
    keys = set()
    type_ = set()
    for bids_object in bids_objects:
        type_.add(bids_object.get_bids_type())
        for key in bids_object.get_metadata().keys():
            keys.add(key)
    return keys, type_
