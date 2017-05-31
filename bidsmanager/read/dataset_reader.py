import glob
import os

from ..read.subject_reader import read_subject
from ..base.dataset import DataSet
from ..utils.utils import read_tsv, read_json


def load_data_set(path_to_dataset):
    dataset = DataSet(path=path_to_dataset, metadata=read_dataset_metadata(path_to_dataset))
    return add_subjects_to_dataset(dataset, path_to_dataset)


def add_subjects_to_dataset(dataset, path_to_dataset):
    [dataset.add_subject(subject) for subject in read_subjects_in_dataset_path(path_to_dataset)]
    return dataset


def read_subjects_in_dataset_path(path_to_dataset):
    return [read_subject(path_to_subject, metadata=read_subjects_metadata(path_to_dataset)) for path_to_subject in
            find_subject_folders(path_to_dataset)]


def find_subject_folders(path_to_data_set):
    return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))


def read_dataset(path_to_dataset):
    return load_data_set(path_to_dataset=path_to_dataset)


def read_subjects_metadata(path_to_dataset):
    metadata_file = os.path.join(path_to_dataset, "participants.tsv")
    if os.path.isfile(metadata_file):
        return read_tsv(metadata_file)


def read_dataset_metadata(path_to_dataset):
    metadata_file = os.path.join(path_to_dataset, "dataset_description.json")
    if os.path.isfile(metadata_file):
        return read_json(metadata_file)
