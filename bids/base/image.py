

class Image(object):
    def __init__(self, file_path=None, side_car_path=None, modality=None):
        self.file_path = file_path
        self.side_car_path = side_car_path
        self._modality = modality

    def get_file_path(self):
        return self.file_path

    def get_modality(self):
        return self._modality


class FunctionalImage(Image):
    def __init__(self, task_name=None, *inputs, **kwargs):
        super(FunctionalImage, self).__init__(*inputs, **kwargs)
        self._task_name = task_name

    def get_task_name(self):
        return self._task_name

