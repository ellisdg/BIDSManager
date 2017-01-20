import glob
import os

from bids.read.subject_reader import read_subject
from ..base.dataset import DataSet


class DataSetReader(object):
    @staticmethod
    def load_data_set(path_to_data_set):
        return DataSet(DataSetReader.get_subject_subjects(path_to_data_set))

    @staticmethod
    def get_subject_subjects(path_to_data_set):
        return [read_subject(path_to_subject) for path_to_subject in DataSetReader.find_subject_folders(path_to_data_set)]

    @staticmethod
    def find_subject_folders(path_to_data_set):
        return sorted(glob.glob(os.path.join(path_to_data_set, "sub-*")))


def read_dataset(path_to_dataset_folder):
    return DataSetReader.load_data_set(path_to_dataset_folder)
