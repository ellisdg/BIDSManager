import os
import re
import glob

from bids.utils.image_utils import load_image


def parse_task_name(path_to_image):
    return parse_generic_name(path_to_image, name="task")


def read_image_from_bids_path(path_to_image):
    modality = parse_image_modality(path_to_image)
    acquisition = parse_generic_name(path_to_image, name="acq")
    task_name = parse_task_name(path_to_image)
    run_number = parse_generic_name(path_to_image, name="run")
    return load_image(path_to_image, modality=modality, acquisition=acquisition, task_name=task_name,
                      run_number=run_number, bval_path=find_sidecar(path_to_image, extension=".bval"),
                      bvec_path=find_sidecar(path_to_image, extension=".bvec"),
                      path_to_sidecar=find_sidecar(path_to_image, extension=".json"))


def find_sidecar(in_file, extension=".json"):
    sidecar_file = in_file.replace(".nii.gz", extension)
    return get_file(sidecar_file)


def get_file(in_file):
    sidecar_files = glob.glob(in_file)
    if len(sidecar_files) == 1:
        return sidecar_files[0]


def parse_generic_name(path_to_image, name):
    result = re.search('(?<={name}-)[a-z0-9]*'.format(name=name), os.path.basename(path_to_image))
    if result:
        return result.group(0)


def parse_image_modality(path_to_image):
    return os.path.basename(path_to_image).split(".")[0].split("_")[-1]


def read_image(path_to_image_file):
    return read_image_from_bids_path(path_to_image_file)
