import os
from unittest import TestCase

from bidsmanager.base.image import Image
from bidsmanager.read import read_dataset
from bidsmanager.utils.epi import set_intended_for


class TestEPI(TestCase):
    def test_intended_for(self):
        bids_dir = os.path.abspath("../BIDS-examples/ds001")
        dataset = read_dataset(bids_dir)
        intended_for_image = dataset.get_images(subject_id="01", modality="bold")[0]
        epi_image = Image(modality="epi")
        set_intended_for(epi_image, intended_for_image)
        _intended_for_path = epi_image.get_metadata("IntendedFor")
        intended_for_path = intended_for_image.get_path().replace(bids_dir, "").replace("sub-01", "", 1).strip("/")
        assert _intended_for_path == intended_for_path

