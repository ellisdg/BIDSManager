import os
import re
import glob

from bidsmanager.base.image import image_entities
from bidsmanager.utils.image_utils import load_image


def parse_path_name(path_to_image, entities=image_entities):
    return {entity: parse_generic_name(path_to_image, entity) for entity in entities}


def parse_task_name(path_to_image):
    return parse_generic_name(path_to_image, name="task")

def parse_entities(path_to_image, entity_specification, **custom_entities):
    entities = custom_entities.copy()
    remaining_entities = set(entity_specification).difference(set(entities.keys()))

    # parse entities that are not specified
    parsed_entities = parse_path_name(path_to_image, remaining_entities)

    entities.update(parsed_entities)
    if "modality" in entities:
        modality = entities.pop("modality")
    else:
        modality = parse_image_modality(path_to_image)
    return modality, entities

def read_image_from_bids_path(path_to_image, metadata_dictionary=None, entity_specification=image_entities,
                              **custom_entities):
    modality, entities = parse_entities(path_to_image, entity_specification, **custom_entities)
    metadata_key = os.path.join(os.path.basename(os.path.dirname(path_to_image)), os.path.basename(path_to_image))
    if metadata_dictionary and metadata_key in metadata_dictionary:
        image_metadata = metadata_dictionary[metadata_key]
    else:
        image_metadata = None
    return load_image(path_to_image, modality=modality, bval_path=find_sidecar(path_to_image, extension=".bval"),
                      bvec_path=find_sidecar(path_to_image, extension=".bvec"),
                      path_to_sidecar=find_sidecar(path_to_image, extension=".json"),
                      metadata=image_metadata, **entities)


def find_sidecar(in_file, extension=".json"):
    sidecar_file = in_file.replace(".nii.gz", extension)
    return get_file(sidecar_file)


def get_file(in_file):
    sidecar_files = glob.glob(in_file)
    if len(sidecar_files) == 1:
        return sidecar_files[0]


def parse_generic_name(path_to_image, name):
    result = re.search('(?<={name}-)[a-z0-9A-Z^]*'.format(name=name), os.path.basename(path_to_image))
    if result:
        return result.group(0)


def parse_image_modality(path_to_image):
    return os.path.basename(path_to_image).split(".")[0].split("_")[-1]


def read_image(path_to_image_file, metadata=None, **custom_entities):
    return read_image_from_bids_path(path_to_image_file, metadata_dictionary=metadata, **custom_entities)
