import os
import re

from bids.utils.image_utils import load_image


class ImageReader(object):
    def read_image_from_bids_path(self, path_to_image):
        modality = self.parse_image_modality(path_to_image)
        acquisition = self.parse_generic_name(path_to_image, name="acq")
        task_name = self.parse_task_name(path_to_image)
        run_number = self.parse_generic_name(path_to_image, name="run")
        return load_image(path_to_image, modality=modality, acquisition=acquisition, task_name=task_name,
                          run_number=run_number)

    @staticmethod
    def parse_image_modality(path_to_image):
        return os.path.basename(path_to_image).split(".")[0].split("_")[-1]

    @staticmethod
    def parse_generic_name(path_to_image, name):
        result = re.search('(?<={name}-)[a-z0-9]*'.format(name=name), os.path.basename(path_to_image))
        if result:
            return result.group(0)

    def parse_task_name(self, path_to_image):
        return self.parse_generic_name(path_to_image, name="task")


def read_image(path_to_image_file):
    return ImageReader().read_image_from_bids_path(path_to_image_file)
