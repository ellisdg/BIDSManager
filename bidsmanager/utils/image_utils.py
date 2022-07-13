from bidsmanager.base.image import Image


def load_image(path_to_image, modality=None, acquisition=None, task_name=None, run_number=None, path_to_sidecar=None,
               bval_path=None, bvec_path=None, metadata=None, **entities):
    return Image(modality=modality, path=path_to_image,
                 sidecar_path=path_to_sidecar, metadata=metadata, bval_path=bval_path, bvec_path=bvec_path,
                 **entities)
