from bidsmanager.base.group import FunctionalGroup, Group


def load_group(path_to_group_folder=None, group_name=None, images=None):
    if group_name == "func":
        return FunctionalGroup(name=group_name, images=images, path=path_to_group_folder)
    else:
        return Group(name=group_name, images=images, path=path_to_group_folder)


def modality_to_group_name(modality):
    if modality in ["FLAIR", "T1w", "T2w"]:
        return "anat"
    elif modality in ["dwi"]:
        return "dwi"
    elif modality in ["bold"]:
        return "func"
    elif modality in ["epi", "sbref"]:
        return "fmap"
    else:
        return "unknown"
