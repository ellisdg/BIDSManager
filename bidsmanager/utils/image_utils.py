from bidsmanager.base.image import FunctionalImage, Image, DiffusionImage


def load_image(path_to_image, modality=None, acquisition=None, task_name=None, run_number=None, path_to_sidecar=None,
               bval_path=None, bvec_path=None):
    if modality == "bold":
        return FunctionalImage(modality=modality,
                               path=path_to_image,
                               acquisition=acquisition,
                               task_name=task_name,
                               run_number=run_number,
                               sidecar_path=path_to_sidecar)
    elif modality == "dwi":
        return DiffusionImage(bval_path=bval_path, bvec_path=bvec_path, path=path_to_image, run_number=run_number,
                              acquisition=acquisition, modality=modality, sidecar_path=path_to_sidecar)
    else:
        return Image(modality=modality, path=path_to_image, acquisition=acquisition, run_number=run_number,
                     sidecar_path=path_to_sidecar)
