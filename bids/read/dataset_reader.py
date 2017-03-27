import glob
import os

from ..read.subject_reader import read_subject
from ..base.dataset import DataSet


class DataSetReader(object):
    @staticmethod
    def load_data_set(path_to_data_set):
        dataset = DataSet(path=path_to_data_set)
        return DataSetReader.add_subjects_to_dataset(dataset)

    @staticmethod
    def add_subjects_to_dataset(dataset):
        [dataset.add_subject(subject) for subject in DataSetReader.read_subjects_in_dataset_path(dataset.get_path())]
        return dataset

    @staticmethod
    def read_subjects_in_dataset_path(path_to_data_set):
        return [read_subject(path_to_subject) for path_to_subject in
                DataSetReader.find_subject_folders(path_to_data_set)]

    @staticmethod
    def find_subject_folders(path_to_data_set):
        return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))


def read_dataset(path_to_dataset_folder):
    return DataSetReader.load_data_set(path_to_dataset_folder)
