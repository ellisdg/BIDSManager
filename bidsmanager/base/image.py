import os

from .base import BIDSObject
from ..utils.utils import update_file, read_json


class Image(BIDSObject):
    def __init__(self, sidecar_path=None, modality=None, acquisition=None, run_number=None, *inputs, **kwargs):
        self._session = None
        self._subject = None
        self._group = None
        super(Image, self).__init__(*inputs, **kwargs)
        self.sidecar_path = sidecar_path
        self.update_metadata()
        self._modality = modality
        self._acquisition = acquisition
        self._run_number = run_number

    def get_basename(self):
        return "_".join(self.get_subject_session_keys(keys=self.get_image_keys())) + self.get_extension()

    def get_extension(self):
        if self._path:
            if ".nii.gz" in self._path:
                return ".nii.gz"
            return os.path.splitext(self._path)[-1]
        return ".nii"

    def get_modality(self):
        return self._modality

    def get_acquisition(self):
        return self._acquisition

    def get_image_keys(self, keys=None):
        if not keys:
            keys = []
        if self._acquisition:
            keys.append("acq-{0}".format(self._acquisition))
        if self._run_number:
            keys.append("run-{0:02d}".format(int(self._run_number)))
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
        return self._run_number

    def get_session_key(self):
        if self._session:
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

    def is_match(self, modality=None, acquisition=None, run_number=None):
        return (not modality or modality == self.get_modality()) \
               and (not acquisition or acquisition == self.get_acquisition()) \
               and (not run_number or int(run_number) == int(self.get_run_number()))

    def set_acquisition(self, acquisition):
        current_key = self.get_image_key()
        self._acquisition = acquisition
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

    def update(self, run=False, move=False):
        if run:
            if self._path and self._previous_path:
                update_file(self._previous_path, self._path, move=move)
            self.update_sidecar(move=move)

    def update_sidecar(self, move=False):
        if self.sidecar_path:
            tmp_sidecar_file = self._path.replace(self.get_extension(), ".json")
            update_file(self.sidecar_path, tmp_sidecar_file, move=move)
            self.sidecar_path = tmp_sidecar_file

    def update_key(self, prev_key):
        if self.get_parent():
            new_key = self.get_image_key()
            self.get_parent().modify_key(prev_key, new_key)

    def read_sidecar(self):
        return read_json(self.sidecar_path)

    def update_metadata(self):
        if self._metadata is None:
            self._metadata = dict()
        if self.sidecar_path:
            for key, value in self.read_sidecar().items():
                self._metadata[key] = value


class FunctionalImage(Image):
    def __init__(self, task_name=None, *inputs, **kwargs):
        super(FunctionalImage, self).__init__(*inputs, **kwargs)
        self._task_name = task_name

    def get_task_name(self):
        return self._task_name

    def set_task_name(self, task_name):
        current_key = self.get_image_key()
        self._task_name = task_name
        self.update_key(current_key)

    def get_image_keys(self, keys=None):
        if not keys:
            keys = []
        if self._task_name:
            keys.append("task-{0}".format(self._task_name.lower().replace(" ", "")))
        return super(FunctionalImage, self).get_image_keys(keys)

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

    def update(self, run=False, move=False):
        super(DiffusionImage, self).update(run=run, move=move)
        self.update_bval(move=move)
        self.update_bvec(move=move)
