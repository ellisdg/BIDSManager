import os

from .base import BIDSObject
from ..utils.utils import update_file, read_json, combine_dictionaries
from ..write.dataset_writer import write_json


class Image(BIDSObject):
    def __init__(self, sidecar_path=None, modality=None, extension=".nii", *inputs, **kwargs):
        self._session = None
        self._subject = None
        self._group = None
        for key in image_entities:
            if key in kwargs:
                setattr(self, "_" + key, kwargs.pop(key))
            else:
                setattr(self, "_" + key, None)
        super(Image, self).__init__(*inputs, **kwargs)
        self.sidecar_path = sidecar_path
        self._sidecar_metadata = dict()
        self.update_sidecar_metadata()
        self._modality = modality
        self._type = "Image"
        self._extension = extension

    def get_basename(self):
        return "_".join(self.get_subject_session_keys(keys=self.get_image_keys())) + self.get_extension()

    def get_extension(self):
        if self._path:
            if ".nii.gz" in self._path:
                return ".nii.gz"
            return os.path.splitext(self._path)[-1]
        return self._extension

    def get_modality(self):
        return self._modality

    def get_acquisition(self):
        return self._acq

    def get_image_keys(self, keys=None):
        if not keys:
            keys = []
        for attribute in image_entities:
            if self._get_key_attribute(attribute):
                if attribute == "run":
                    keys.append("{}-{:02d}".format(attribute, int(self.get_run_number())))
                else:
                    keys.append(attribute + "-" + str(self._get_key_attribute(attribute).replace(" ", "")))

        if self._modality:
            keys.append(self._modality)
        return keys

    def get_image_key(self, keys=None):
        return "_".join(self.get_image_keys(keys=keys))

    def get_subject_session_keys(self, keys=None):
        if not keys:
            keys = []
        subject_key = self.get_subject_key()
        if subject_key:
            keys.insert(0, subject_key)
        session_key = self.get_session_key()
        if session_key:
            keys.insert(1, session_key)
        return keys

    def get_run_number(self):
        return self._run

    def get_session_key(self):
        if self._session and self._session.get_name():
            return self._session.get_basename()

    def get_session(self):
        return self._session

    def get_subject(self):
        return self._subject

    def get_subject_key(self):
        if self._subject:
            return self._subject.get_basename()

    def get_group(self):
        return self._group

    def get_metadata(self, key=None):
        metadata = combine_dictionaries(self._sidecar_metadata, super(Image, self).get_metadata())
        if key:
            return metadata[key]
        return metadata

    def get_tsv_metadata(self, key=None):
        return super(Image, self).get_metadata(key=key)

    def get_direction(self):
        return self._dir

    def get_contrast(self):
        return self._ce

    def get_reconstruction(self):
        return self._rec

    def get_entity(self, entity):
        return getattr(self, "_" + entity)

    def get_sidecar_metadata(self, key):
        return self._sidecar_metadata[key]

    def is_match(self, **kwargs):
        return all((entity not in kwargs
                    or self.get_entity(entity) == kwargs[entity]
                    or (not self.get_entity(entity) and not kwargs[entity])
                    for entity in image_entities + ("modality",)))

    def set_acquisition(self, acquisition):
        current_key = self.get_image_key()
        self._acq = acquisition
        self.update_key(current_key)

    def set_parent(self, parent):
        super(Image, self).set_parent(parent)
        self._group = self._parent
        if self._group:
            session = self._group.get_parent()
            self.set_session(session)

    def set_session(self, session):
        from bidsmanager.base import Session, Subject
        if isinstance(session, Session):
            self._session = session
            self._subject = session.get_parent()
        elif isinstance(session, Subject):
            self._subject = session

    def set_direction(self, direction):
        self._set_key_attribute("_dir", direction)

    def set_modality(self, modality):
        self._set_key_attribute("_modality", modality)

    def set_run_number(self, run_number):
        self._set_key_attribute("_run", run_number)

    def set_task_name(self, task_name):
        self._set_key_attribute("_task", task_name)

    def set_contrast(self, contrast):
        self._set_key_attribute("_ce", contrast)

    def set_reconstruction(self, reconstruction):
        self._set_key_attribute("_rec", reconstruction)

    def update(self, move=False):
        if os.path.basename(self.get_path()) != self.get_basename():
            self.set_path(os.path.join(os.path.dirname(self.get_path()), self.get_basename()))
        update_file(self._previous_path, self._path, move=move)
        self.update_sidecar(move=move)

    def update_sidecar(self, move=False):
        if self._sidecar_metadata:
            tmp_sidecar_file = self._path.replace(self.get_extension(), ".json")
            if self.sidecar_path is None or self._sidecar_metadata != self.read_sidecar():
                write_json(self._sidecar_metadata, tmp_sidecar_file)
                if move and self.sidecar_path and self.sidecar_path != tmp_sidecar_file:
                    os.remove(self.sidecar_path)
            else:
                update_file(self.sidecar_path, tmp_sidecar_file, move=move)
            self.sidecar_path = tmp_sidecar_file

    def update_key(self, prev_key):
        if self.get_parent():
            new_key = self.get_image_key()
            self.get_parent().modify_key(prev_key, new_key)

    def read_sidecar(self):
        return read_json(self.sidecar_path)

    def update_sidecar_metadata(self):
        if self.sidecar_path:
            for key, value in self.read_sidecar().items():
                self.add_sidecar_metadata(key, value)

    def add_metadata(self, key, value, sidecar=True):
        if sidecar:
            self.add_sidecar_metadata(key, value)
        else:
            super(Image, self).add_metadata(key, value)

    def add_sidecar_metadata(self, key, value):
        self._sidecar_metadata[key] = value

    def get_task_name(self):
        return self._task

    def _get_key_attribute(self, attribute):
        return getattr(self, "_" + attribute)

    def _set_key_attribute(self, attribute, value):
        current_key = self.get_image_key()
        setattr(self, attribute, value)
        self.update_key(current_key)


class FunctionalImage(Image):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalImage, self).__init__(*inputs, **kwargs)

    def is_match(self, task_name=None, **kwargs):
        return (not task_name or task_name == self.get_task_name()) and super(FunctionalImage, self).is_match(**kwargs)


class DiffusionImage(Image):
    def __init__(self, bval_path, bvec_path, *inputs, **kwargs):
        super(DiffusionImage, self).__init__(*inputs, **kwargs)
        self._bval_path = bval_path
        self._bvec_path = bvec_path
        self._modality = "dwi"

    def update_bval(self, move=False):
        tmp_bval_file = self.get_path().replace(self.get_extension(), ".bval")
        update_file(self._bval_path, tmp_bval_file, move=move)
        self._bval_path = tmp_bval_file

    def update_bvec(self, move=False):
        tmp_bvec_file = self.get_path().replace(self.get_extension(), ".bvec")
        update_file(self._bvec_path, tmp_bvec_file, move=move)
        self._bvec_path = tmp_bvec_file

    def update(self, *args, **kwargs):
        super(DiffusionImage, self).update(*args, **kwargs)
        if self._bval_path:
            self.update_bval(*args, **kwargs)
        if self._bvec_path:
            self.update_bvec(*args, **kwargs)


image_entities = ("task", "acq", "ce", "dir", "rec",  "run", "echo")
