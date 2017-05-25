import filecmp
import shutil
import os

import pandas as pd


def update_file(old_file, new_file, move=False):
    if not os.path.exists(new_file) or not filecmp.cmp(old_file, new_file):
        copy_or_move(old_file, new_file, move=move)


def copy_or_move(in_file, out_file, move=False):
    if move:
        shutil.move(in_file, out_file)
    else:
        shutil.copy(in_file, out_file)


def read_tsv(in_file):
    data = dict()
    with open(in_file, "rU") as tsv_file:
        for i, line in enumerate(tsv_file):
            row = line.strip().split("\t")
            if i == 0:
                header = row
            else:
                row_data = dict()
                # assumes all rows are the same length
                for index in range(1, len(row)):
                    row_data[header[index]] = parse_input(row[index])
                # assumes the first column to be the id column
                key = row[0]
                data[key] = row_data
    return data


def parse_input(string):
    try:
        return pd.to_datetime(string).date()
    except ValueError:
        return parse_float(string)


def parse_float(string):
    try:
        return float(string)
    except ValueError:
        return string
