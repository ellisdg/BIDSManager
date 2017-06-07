import os
import json
from datetime import datetime
import copy


def write_dataset(dataset, output_dir, move=False):
    dataset = copy.deepcopy(dataset)
    dataset.set_path(os.path.abspath(output_dir))
    dataset.update(move=move)
    return dataset


def make_dirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_tsv(data_dict, out_file, first_colum="id"):
    columns = get_all_sub_keys(data_dict)
    with open(out_file, "w") as opened_file:
        header = [first_colum] + list(columns)
        write_tsv_row(header, opened_file)
        for key, value in data_dict.items():
            column_values = list()
            for column in columns:
                if column in value:
                    column_values.append(data_value_to_string(value[column]))
                else:
                    column_values.append("")
            row = [key] + column_values
            write_tsv_row(row, opened_file)


def data_value_to_string(data):
    if isinstance(data, datetime):
        try:
            return datetime.strftime(data, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}".format(year=data.year,
                                                                                                  month=data.month,
                                                                                                  day=data.day,
                                                                                                  hour=data.hour,
                                                                                                  minute=data.minute,
                                                                                                  second=data.second)
    else:
        return str(data)


def write_json(data, out_file):
    with open(out_file, "w") as opened_file:
        json.dump(data, opened_file)


def write_tsv_row(row, opened_file):
    opened_file.write("\t".join(row) + "\n")


def get_all_sub_keys(data_dict):
    keys = set()
    for value in data_dict.values():
        for key in value.keys():
            keys.add(key)
    return keys
