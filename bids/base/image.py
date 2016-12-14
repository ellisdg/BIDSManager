import os
import re


class Image(object):
    def __init__(self, file_path=None, side_car_path=None):
        self.file_path = file_path
        self.side_car_path = side_car_path

    def get_file_path(self):
        return self.file_path


class FunctionalImage(Image):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalImage, self).__init__(*inputs, **kwargs)
        self._task_name = self._resolve_task_name()

    def _resolve_task_name(self):
        return re.search('(?<=task-)[a-z]*', os.path.basename(self.file_path)).group(0)

    def get_task_name(self):
        return self._task_name

