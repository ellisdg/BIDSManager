from bids.base.image import FunctionalImage, Image


def load_image(path_to_image, modality=None, acquisition=None, task_name=None, run_number=None, path_to_sidecar=None):
    if modality == "bold":
        return FunctionalImage(modality=modality,
                               path=path_to_image,
                               acquisition=acquisition,
                               task_name=task_name,
                               run_number=run_number,
                               sidecar_path=path_to_sidecar)
    else:
        return Image(modality=modality, path=path_to_image, acquisition=acquisition, run_number=run_number,
                     sidecar_path=path_to_sidecar)