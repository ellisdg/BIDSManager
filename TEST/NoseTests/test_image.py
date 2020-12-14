import os
from unittest import TestCase

from bidsmanager.base.group import Group
from bidsmanager.base.image import Image, FunctionalImage, DiffusionImage
from bidsmanager.read.image_reader import read_image_from_bids_path
from bidsmanager.write.dataset_writer import write_json
from bidsmanager.utils.utils import read_json


def touch(tmp_file):
    with open(tmp_file, "w") as opened_file:
        print("creating: " + tmp_file)
        return opened_file


class TestImage(TestCase):
    def test_change_acquisition(self):
        image = Image(modality="T1w", acq="contrast")
        basename = image.get_basename()
        image.set_acquisition("postcontrast")
        self.assertEqual(basename.replace("contrast", "postcontrast"), image.get_basename())

    def test_change_task_name(self):
        image = FunctionalImage(modality="bold", task="prediction", run=3)
        basename = image.get_basename()
        image.set_task_name("weatherprediction")
        self.assertEqual(basename.replace("prediction", "weatherprediction"), image.get_basename())

    def test_write_changed_acquisition(self):
        tmp_file = "run-05_FLAIR.nii.gz"
        self.touch(tmp_file)
        new_tmp_file = "acq-contrast_" + tmp_file
        self.assertTrue(os.path.exists(tmp_file))
        try:
            image = read_image_from_bids_path(tmp_file)
            image.set_acquisition("contrast")
            image.update(move=True)
            self.assertFalse(os.path.exists(tmp_file))
            self.assertTrue(os.path.exists(new_tmp_file))
            os.remove(new_tmp_file)
        except AssertionError as error:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            if os.path.exists(new_tmp_file):
                os.remove(new_tmp_file)
            raise error

    def test_write_metadata(self):
        tmp_file = "run-05_FLAIR.nii.gz"
        self.touch(tmp_file)
        tmp_json = "run-05_FLAIR.json"
        self._filenames_to_delete.add(tmp_json)
        json_data = {"the_answer": 42}
        write_json(json_data, tmp_json)
        image = read_image_from_bids_path(tmp_file)
        self.assertEqual(image.get_metadata(), json_data)

        image._run = 6
        image.update(move=False)
        self._filenames_to_delete.add(image.get_path())
        self._filenames_to_delete.add(image.sidecar_path)
        self.assertEqual(image.get_metadata(), json_data)
        self.assertTrue(os.path.exists(image.sidecar_path))

        prev_sidecar_path = image.sidecar_path
        image._run = 7
        image.update(move=True)
        self._filenames_to_delete.add(image.get_path())
        self._filenames_to_delete.add(image.sidecar_path)
        self.assertEqual(image.get_metadata(), json_data)
        self.assertFalse(os.path.exists(prev_sidecar_path))

    def test_add_sidecar_metadata(self):
        image_filename = "acq-contrast_T1w.nii.gz"
        self.touch(image_filename)
        image = Image(path=image_filename, acq='contrast', modality='T1w')
        key = 'delete_file'
        value = True
        image.add_sidecar_metadata(key, value)
        image.update(move=True)
        self._filenames_to_delete.add(image.sidecar_path)
        self._filenames_to_delete.add(image.get_path())
        sidecar_path = image_filename.replace('.nii.gz', '.json')
        self.assertTrue(os.path.exists(sidecar_path))
        sidecar_metadata = read_json(sidecar_path)
        self.assertDictEqual(image.get_metadata(), sidecar_metadata)
        self.assertEqual(sidecar_metadata[key], value)

        self._filenames_to_delete.add(sidecar_path)

    def test_add_phase_encoding_direction(self):
        image = Image(dir="AP", extension=".nii.gz")
        assert "dir-AP" in image.get_basename()
        assert "AP" == image.get_direction()
        image.set_direction("LR")
        assert "dir-LR" in image.get_basename()
        image.set_run_number(2)
        image.set_acquisition("test")
        image.set_modality("bogus")
        assert image.get_basename() == "acq-test_dir-LR_run-02_bogus.nii.gz"

    def test_task_name(self):
        image = Image()
        image.set_task_name("rest")
        assert image.get_task_name() == "rest"
        assert "task-rest" in image.get_basename()
        group = Group()
        group.add_image(image)
        image.set_run_number(5)
        image.set_direction("PA")
        image.set_task_name("science")
        assert image.get_task_name() == "science"

    def test_contrast(self):
        image = Image(modality="T1w")
        image.set_contrast("gad")
        assert image.get_contrast() == "gad"
        assert "ce-gad" in image.get_basename()

    def test_reconstruction(self):
        image = Image(modality="T1w")
        image.set_reconstruction("axial")
        assert image.get_reconstruction() == "axial"
        assert "rec-axial" in image.get_basename()

    def test_add_metadata_without_sidecar(self):
        image = DiffusionImage(modality="dwi", bval_path="./bval", bvec_path="./bvec")
        image.add_metadata("WellThoughtOutTest", False)
        image.set_path("./test.nii.gz")
        touch(image.get_path())
        touch(image.get_bval_path())
        touch(image.get_bvec_path())
        image.set_direction("AP")
        image.update(move=True)
        assert not os.path.exists("./test.nii.gz")
        assert not os.path.exists("./bvec")
        assert not os.path.exists("./bval")
        assert os.path.exists(image.get_path())
        assert os.path.exists(image.get_bval_path())
        assert os.path.exists(image.get_bvec_path())
        for fn in (image.get_path(), image.get_bval_path(), image.get_bvec_path(), image.get_sidecar_path()):
            os.remove(fn)

    def touch(self, filename):
        touch(filename)
        self._filenames_to_delete.add(filename)

    def setUp(self):
        self._filenames_to_delete = set()

    def tearDown(self):
        for filename in self._filenames_to_delete:
            if filename is not None and os.path.exists(filename):
                os.remove(filename)
