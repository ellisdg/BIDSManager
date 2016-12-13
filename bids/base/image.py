class Image(object):
    def __init__(self, file_path=None, side_car_path=None):
        self.file_path = file_path
        self.side_car_path = side_car_path

    def get_file_path(self):
        return self.file_path

