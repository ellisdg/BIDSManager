import filecmp
import shutil
import os
import json

import pandas as pd


def update_file(old_file, new_file, move=False):
    if not os.path.exists(new_file) or (old_file is not None and not filecmp.cmp(old_file, new_file)):
        copy_or_move(old_file, new_file, move=move)


def copy_or_move(in_file, out_file, move=False):
    if move == 'link':
        os.symlink(in_file, out_file)
    elif move is True:
        shutil.move(in_file, out_file)
    else:
        shutil.copy(in_file, out_file)


def read_json(in_file):
    with open(in_file , "r") as opened_file:
        return json.load(opened_file)


def read_tsv(in_file):
    data = dict()
    with open(in_file, "r") as tsv_file:
        for i, line in enumerate(tsv_file):
            row = line.strip().split("\t")
            if i == 0:
                header = row
            else:
                row_data = dict()
                # assumes all rows are the same length
                for index in range(1, len(row)):
                    value = row[index]
                    if value:
                        row_data[header[index]] = parse_input(value)
                # assumes the first column to be the id column
                key = row[0]
                data[key] = row_data
    return data


def parse_input(string):
    try:
        datetime_ = pd.to_datetime(string)
        if datetime_.hour == 0 and datetime_.minute == 0 and datetime_.second == 0:
            return datetime_.date()
        else:
            return datetime_
    except ValueError:
        return parse_float(string)


def parse_float(string):
    try:
        return float(string)
    except ValueError:
        return string


def combine_dictionaries(dict1, dict2):
    new_dict = dict1.copy()
    new_dict.update(dict2)
    return new_dict
