import glob
import os

from .base import BIDSFolder


class Group(BIDSFolder):
    def __init__(self, *inputs, images=None, **kwargs):
        self._flags = dict()
        super(Group, self).__init__(*inputs, **kwargs)
        self._images = self._dict
        self._type = "Group"
        if images:
            self.add_images(images)

    def add_image(self, image):
        image_key = image.get_image_key()
        if image_key in self._flags:
            self._flags[image_key] += 1
            image._run = self._flags[image_key]
            image_key = image.get_image_key()
        try:
            self._add_object(image, image_key, "Image")
        except KeyError:
            self._flags[image_key] = 0
            self.add_images([self._images.pop(image_key), image])

    def add_images(self, images):
        for image in images:
            self.add_image(image)

    def get_name(self):
        return self._name

    def get_basename(self):
        return self.get_name()

    def get_images(self, **kwargs):
        images = []
        for image in self._images.values():
            if image.is_match(**kwargs):
                images.append(image)
        return images

    def get_modalities(self):
        return [image.get_modality() for image in self._images.values()]

    def get_all_images(self):
        return list(self._images.values())

    def normalize_runs_for_write(self):
        # Build runless buckets; singleton buckets should not carry a run label in the final filename.
        images_by_signature = {}
        for image in list(self._images.values()):
            signature = (
                image.get_task_name(),
                image.get_acquisition(),
                image.get_contrast(),
                image.get_direction(),
                image.get_reconstruction(),
                image.get_entity("echo"),
                image.get_modality(),
            )
            images_by_signature.setdefault(signature, []).append(image)

        for images in images_by_signature.values():
            if len(images) == 1 and images[0].get_run_number() is not None:
                images[0].set_run_number(None)

    def _assign_run_numbers_for_write(self):
        reserved_paths = set()
        for image in list(self.get_images()):
            self._assign_run_number_for_image(image=image, reserved_paths=reserved_paths)

    def _assign_run_number_for_image(self, image, reserved_paths):
        run_number = image.get_run_number()
        while True:
            candidate_path = os.path.join(self.get_path(), image.get_basename())
            current_path = None
            try:
                current_path = image.get_path()
            except ValueError:
                pass

            run_pattern = None
            if run_number is None:
                run_pattern = self._image_run_pattern(image)

            if candidate_path not in reserved_paths and (
                candidate_path == current_path
                or (not os.path.exists(candidate_path) and (run_pattern is None or not glob.glob(run_pattern)))
            ):
                reserved_paths.add(candidate_path)
                return

            run_number = 1 if run_number is None else run_number + 1
            image.set_run_number(run_number)

    def _image_run_pattern(self, image):
        basename_parts = []
        subject_key = image.get_subject_key()
        if subject_key:
            basename_parts.append(subject_key)
        session_key = image.get_session_key()
        if session_key:
            basename_parts.append(session_key)

        for attribute in ("task", "acq", "ce", "dir", "rec"):
            value = image.get_entity(attribute)
            if value:
                basename_parts.append("{}-{}".format(attribute, str(value).replace(" ", "")))
        basename_parts.append("run-*")
        echo = image.get_entity("echo")
        if echo:
            basename_parts.append("echo-{}".format(str(echo).replace(" ", "")))
        basename_parts.append(image.get_modality())

        return os.path.join(self.get_path(), "_".join(basename_parts) + image.get_extension())

    def update(self, move=False):
        self.normalize_runs_for_write()
        self._assign_run_numbers_for_write()
        super(Group, self).update(move=move)


class FunctionalGroup(Group):
    def __init__(self, *inputs, **kwargs):
        super(FunctionalGroup, self).__init__(*inputs, **kwargs)

    def get_task_names(self):
        return [image.get_task_name() for image in self._images.values()]
