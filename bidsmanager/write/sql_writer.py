import sqlite3


def connect_to_database(sql_file):
    return sqlite3.connect(sql_file)


def execute_statement(connection, sql_statement):
    return connection.cursor().execute(sql_statement)
