import os
import json


def write_dataset(dataset, output_dir, move=False):
    dataset.set_path(os.path.abspath(output_dir))
    dataset.update(run=True, move=move)


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
                    column_values.append(str(value[column]))
                else:
                    column_values.append("")
            row = [key] + column_values
            write_tsv_row(row, opened_file)


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
