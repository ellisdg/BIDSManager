import os


def write_dataset(dataset, output_dir):
    dataset.set_path(os.path.abspath(output_dir))
    dataset.update(run=True)


def make_dirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
