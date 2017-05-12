import os


def write_dataset(dataset, output_dir, move=False):
    dataset.set_path(os.path.abspath(output_dir))
    dataset.update(run=True, move=move)


def make_dirs(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
