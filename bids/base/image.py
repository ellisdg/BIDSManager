import os
import shutil

from .base import BIDSObject
from .session import Session
from .subject import Subject


class Image(BIDSObject):
    def __init__(self, side_car_path=None, modality=None, acquisition=None, run_number=None, *inputs, **kwargs):
        self._session = None
        self._subject = None
        self._group = None
        super(Image, self).__init__(*inputs, **kwargs)
        self.side_car_path = side_car_path
        self._modality = modality
        self._acquisition = acquisition
        self._run_number = run_number

    def get_basename(self):
        return self.get_image_key() + self.get_extension()

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

    def get_image_key(self, keys=None):
        if not keys:
            keys = []
        subject_key = self.get_subject_key()
        if subject_key:
            keys.insert(0, subject_key)
        session_key = self.get_session_key()
        if session_key:
            keys.insert(1, session_key)
        if self._acquisition:
            keys.append("acq-{0}".format(self._acquisition))
        if self._run_number:
            keys.append("run-{0}".format(self._run_number))
        if self._modality:
            keys.append(self._modality)
        return "_".join(keys)

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

    def set_parent(self, parent):
        super(Image, self).set_parent(parent)
        self._group = self._parent
        if self._group:
            session = self._group.get_parent()
            if isinstance(session, Session):
                self._session = session
                self._subject = session.get_parent()
            elif isinstance(session, Subject):
                self._subject = session

    def update(self, run=False):
        if run and self._path and not os.path.exists(self._path) and self._previous_path:
            shutil.copy(self._previous_path, self._path)


class FunctionalImage(Image):
    def __init__(self, task_name=None, *inputs, **kwargs):
        super(FunctionalImage, self).__init__(*inputs, **kwargs)
        self._task_name = task_name

    def get_task_name(self):
        return self._task_name

    def get_image_key(self, keys=None):
        if not keys:
            keys = []
        if self._task_name:
            keys.append("task-{0}".format(self._task_name.lower().replace(" ", "")))
        return super(FunctionalImage, self).get_image_key(keys)
