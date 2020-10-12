from bidsmanager.base.image import FunctionalImage, Image, DiffusionImage


def load_image(path_to_image, modality=None, acquisition=None, task_name=None, run_number=None, path_to_sidecar=None,
               bval_path=None, bvec_path=None, metadata=None, **entities):
    if modality == "bold":
        return FunctionalImage(modality=modality,
                               path=path_to_image,
                               sidecar_path=path_to_sidecar,
                               metadata=metadata,
                               **entities)
    elif modality == "dwi":
        return DiffusionImage(bval_path=bval_path, bvec_path=bvec_path, path=path_to_image, modality=modality,
                              sidecar_path=path_to_sidecar,
                              metadata=metadata,
                              **entities)
    else:
        return Image(modality=modality, path=path_to_image,
                     sidecar_path=path_to_sidecar, metadata=metadata, **entities)
