import os
import glob
import re
from subprocess import Popen, PIPE
import random
from warnings import warn
import datetime
import csv
import shutil

from ..base.subject import Subject
from ..base.dataset import DataSet
from ..base.session import Session
from ..utils.image_utils import load_image
from ..utils.session_utils import modality_to_group_name


def _matches_series_description(pattern, description, case_sensitive=False):
    if description is None:
        return False
    if not case_sensitive:
        pattern = pattern.lower()
        description = description.lower()
    return pattern in description


def _matches_series_number(pattern, series_number):
    if series_number is None:
        return False
    return re.search(pattern, str(series_number)) is not None


def parse_image_keys(in_file, description, series_number, heuristic, case_sensitive=False):
    """
    Parse the image description (and in the future other image information) to
    determine the bids keys based on a heuristic provided by the user.
    :param in_file: nifti file output from dcm2niix
    :param description: Series Description provided in the filename from dcm2niix
    :param series_number: Series Number provided in the filename from dcm2niix
    :param heuristic: user provided heuristic to get the keys from the image information
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive.
    :return: image_keys in dictionary format (will be None if image should be skipped)
    """
    image_keys = dict()
    for test_heuristic, test_keys in heuristic.get("SeriesDescription", []):
        if _matches_series_description(test_heuristic, description, case_sensitive=case_sensitive):
            if test_keys is None:
                print("{} found in {}. Skipping: {}".format(test_heuristic,
                                                            description,
                                                            in_file))
                return None
            image_keys.update(test_keys)

    for test_heuristic, test_keys in heuristic.get("SeriesNumber", []):
        if _matches_series_number(test_heuristic, series_number):
            if test_keys is None:
                print("{} found in {}. Skipping: {}".format(test_heuristic,
                                                            series_number,
                                                            in_file))
                return None
            image_keys.update(test_keys)

    if "modality" not in image_keys:
        # each valid image must have a modality
        warn(RuntimeWarning("No modality found for converted image: {}".format(in_file)))
        return None
    return image_keys


def manipulate_path_extension(in_file, in_ext, out_ext):
    return in_file.replace(in_ext, out_ext)


def get_secondary_output(primary_file, primary_ext, secondary_ext):
    secondary_file = manipulate_path_extension(primary_file, primary_ext, secondary_ext)
    if os.path.exists(secondary_file):
        return secondary_file


def parse_output(in_file, separator):
    return os.path.basename(in_file).split(separator)


def get_image(in_file, separator, heuristic, case_sensitive=False):
    """
    Get the image from the dcm2niix output file in BIDSManager format.
    :param in_file:
    :param separator:
    :param heuristic:
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive.
    :return:
    """
    subject_name, time, description, protocol, series_number, run = parse_output(in_file, separator)
    _ = (subject_name, protocol, run)
    image_keys = parse_image_keys(
        in_file,
        description,
        series_number,
        heuristic=heuristic,
        case_sensitive=case_sensitive,
    )
    # returns None if no image modality is found or image is to be skipped
    if image_keys:
        bval_path = get_secondary_output(in_file, ".nii.gz", ".bval")
        bvec_path = get_secondary_output(in_file, ".nii.gz", ".bvec")
        sidecar_path = get_secondary_output(in_file, ".nii.gz", ".json")
        return load_image(path_to_image=in_file, bval_path=bval_path, bvec_path=bvec_path,
                          path_to_sidecar=sidecar_path, **image_keys)


def _normalize_mapping_value(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith(".0"):
        try:
            return str(int(float(text)))
        except ValueError:
            return text
    return text


def _read_mapping_rows(subject_map=None):
    rows = []
    if not subject_map:
        return rows
    if not os.path.exists(subject_map):
        warn(RuntimeWarning("Subject mapping file not found: {}".format(subject_map)))
        return rows

    extension = os.path.splitext(subject_map)[-1].lower()
    if extension == ".csv":
        with open(subject_map, "r") as f:
            reader = csv.DictReader(f)
            rows.extend(list(reader))
        return rows

    if extension in (".xls", ".xlsx"):
        try:
            import pandas as pd
            frame = pd.read_excel(subject_map)
            rows.extend(frame.to_dict(orient="records"))
        except Exception as exc:
            warn(RuntimeWarning("Could not read subject mapping excel file {}: {}".format(subject_map, exc)))
            # Fallback for lightweight test environments: treat file as CSV-like text.
            try:
                with open(subject_map, "r") as f:
                    reader = csv.DictReader(f)
                    rows.extend(list(reader))
            except Exception:
                pass
        return rows

    warn(RuntimeWarning("Unsupported subject mapping extension for {}. Expected .csv/.xls/.xlsx".format(subject_map)))
    return rows


def _canonical_source_id(value):
    normalized = _normalize_mapping_value(value)
    if normalized is None:
        return None
    # Excel often drops leading zeros for numeric-like IDs; canonicalize to numeric string.
    if normalized.isdigit():
        return str(int(normalized))
    return normalized


_SOURCE_ID_TO_COLUMN = {
    "patient_name": "source_patient_name",
    "patient_id": "source_patient_id",
}


def _normalize_source_ids(source_ids):
    if source_ids is None:
        return []
    normalized = []
    for source_id in source_ids:
        if source_id not in _SOURCE_ID_TO_COLUMN:
            raise ValueError("Unsupported source-id '{}'. Expected one of {}".format(
                source_id,
                sorted(_SOURCE_ID_TO_COLUMN.keys()),
            ))
        normalized.append(source_id)
    return normalized


def _source_id_candidates(value):
    normalized = _normalize_mapping_value(value)
    if normalized is None:
        return []
    canonical = _canonical_source_id(normalized)
    if canonical and canonical != normalized:
        return [normalized, canonical]
    return [normalized]


def _index_dicom_metadata(input_directory):
    metadata_by_series_uid = {}
    try:
        import pydicom
    except Exception:
        return metadata_by_series_uid

    all_files = glob.glob(os.path.join(input_directory, "**", "*"), recursive=True)
    for file_path in all_files:
        if not os.path.isfile(file_path):
            continue
        try:
            dicom = pydicom.dcmread(file_path, stop_before_pixels=True)
        except Exception:
            continue
        series_uid = _normalize_mapping_value(getattr(dicom, "SeriesInstanceUID", None))
        if not series_uid:
            continue
        if series_uid in metadata_by_series_uid:
            continue
        metadata_by_series_uid[series_uid] = {
            "patient_name": _normalize_mapping_value(getattr(dicom, "PatientName", None)),
            "patient_id": _normalize_mapping_value(getattr(dicom, "PatientID", None)),
        }
    return metadata_by_series_uid


def _build_subject_session_mapping(subject_map=None, source_ids=None):
    subject_map_dict = {}
    session_map_dict = {}
    normalized_source_ids = _normalize_source_ids(source_ids)
    rows = _read_mapping_rows(subject_map=subject_map)
    if rows and not normalized_source_ids:
        raise ValueError("subject_map was provided but no --source-id values were supplied.")

    for row in rows:
        bids_subject = _normalize_mapping_value(row.get("bids_subject") or row.get("subject_id") or row.get("bids_id"))
        session_id = _normalize_mapping_value(row.get("session_id") or row.get("session") or row.get("ses"))
        for source_id in normalized_source_ids:
            source_column = _SOURCE_ID_TO_COLUMN[source_id]
            source_value = _normalize_mapping_value(row.get(source_column))
            if source_id == "patient_name" and source_value is None:
                source_value = _normalize_mapping_value(row.get("source_subject"))
            for source_candidate in _source_id_candidates(source_value):
                key = (source_id, source_candidate)
                if bids_subject:
                    subject_map_dict[key] = bids_subject
                if session_id:
                    session_map_dict[key] = session_id
    return subject_map_dict, session_map_dict


def _write_unmatched_source_ids(unmatched_rows, bids_directory, input_directory):
    source_dir = os.path.join(bids_directory if bids_directory else input_directory, "source")
    os.makedirs(source_dir, exist_ok=True)
    output_csv = os.path.join(source_dir, "unmatched_source_ids.csv")
    fieldnames = ["nifti_file", "series_instance_uid", "patient_name", "patient_id", "requested_source_ids"]
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in unmatched_rows:
            writer.writerow(row)
    print("Unmatched source IDs ({} rows):".format(len(unmatched_rows)))
    for row in unmatched_rows:
        print(row)
    print("Wrote unmatched source IDs to {}".format(output_csv))
    return output_csv


def _session_from_time(time_value):
    try:
        acquisition_date = datetime.datetime.strptime(time_value, "%Y%m%d%H%M%S")
        return acquisition_date.strftime("%Y%m%d")
    except ValueError:
        warn(RuntimeWarning("Invalid time format: {}. Using empty session name.".format(time_value)))
        return ""


def _path_exists_for_image(image, subject_name, session_name, bids_directory):
    if not bids_directory:
        return False
    group_name = modality_to_group_name(image.get_modality())
    parts = [bids_directory, "sub-{}".format(subject_name)]
    if session_name:
        parts.append("ses-{}".format(session_name))
    parts.append(group_name)

    # Image is not attached to a Session yet, so build the final BIDS basename explicitly.
    basename_parts = ["sub-{}".format(subject_name)]
    if session_name:
        basename_parts.append("ses-{}".format(session_name))
    basename_parts.append(image.get_image_key())
    out_file = os.path.join(*parts, "_".join(basename_parts) + image.get_extension())
    return os.path.exists(out_file)


def _increment_run_until_unique(image, session, subject_name, session_name, bids_directory):
    # Keep incrementing run until neither the in-memory session nor the output filesystem has a conflict.
    run_number = image.get_run_number() if image.get_run_number() else 1
    image.set_run_number(run_number)
    while session.get_images(modality=image.get_modality(), task=image.get_task_name(),
                             acq=image.get_acquisition(), ce=image.get_contrast(), dir=image.get_direction(),
                             rec=image.get_reconstruction(), run=image.get_run_number()) or \
            _path_exists_for_image(image, subject_name, session_name, bids_directory):
        run_number += 1
        image.set_run_number(run_number)


def convert_dicom_directory(input_directory,
                            heuristic,
                            anonymize=True,
                            separator="---",
                            bids_directory=None,
                            delete_intermediates=True,
                            cleanup_temp_directory=True,
                            verbose=False,
                            use_session_dates=False,
                            combine_sessions=False,
                            subject_map=None,
                            source_ids=None,
                            case_sensitive=False):
    """
    Convert a directory of DICOM files to BIDS format using dcm2niix.
    :param input_directory:
    :param heuristic:
    :param anonymize:
    :param separator:
    :param bids_directory:
    :param delete_intermediates:
    :param cleanup_temp_directory: If True, delete the temporary dcm2niix output directory after conversion.
    :param verbose:
    :param use_session_dates: If True, use the acquisition date to create session names.
    :param combine_sessions: If True, put all images for a subject in a single no-session directory.
    :param subject_map: CSV/XLS/XLSX mapping file for source identifiers -> bids_subject/session.
    :param source_ids: Ordered source identifier list (e.g., ["patient_id", "patient_name"]).
        - patient_id maps to DICOM PatientID (0010,0020), same conceptual field as dcm2niix %i.
          This value is site-defined and is not guaranteed to be MRN.
        - patient_name maps to DICOM PatientName (0010,0010) and is matched as an exact string.
    :param case_sensitive: If True, matching of SeriesDescription will be case sensitive. (default: False)
    :return:
    """
    output_directory = random_tmp_directory()
    dataset = DataSet()
    try:
        dicom_metadata_by_series_uid = _index_dicom_metadata(input_directory)
        run_dcm2niix_on_directory(
            input_directory,
            output_directory,
                filename="%j{0}%t{0}%d{0}%p{0}%s{0}".format(separator),
            anonymize=anonymize,
            verbose=verbose,
        )
        output_niftis = sorted(glob.glob(os.path.join(output_directory, "*.nii.gz")))

        # Heuristic-level mapping paths are supported for backwards compatibility.
        if subject_map is None:
            subject_map = heuristic.get("subject_map")
        # Backward compatibility for older heuristic keys.
        if subject_map is None:
            subject_map = heuristic.get("subject_map_csv") or heuristic.get("subject_map_excel")

        if source_ids is None:
            source_ids = heuristic.get("source_id")
        if isinstance(source_ids, str):
            source_ids = [source_ids]
        source_ids = _normalize_source_ids(source_ids)

        subject_name_map, session_name_map = _build_subject_session_mapping(
            subject_map=subject_map,
            source_ids=source_ids,
        )
        unmatched_rows = []

        for f in output_niftis:
            source_series_uid, time, description, protocol, series_number, run = parse_output(f, separator)
            _ = (description, protocol, series_number, run)

            metadata = dicom_metadata_by_series_uid.get(source_series_uid, {})
            source_values = {
                "patient_name": _normalize_mapping_value(metadata.get("patient_name") or source_series_uid),
                "patient_id": _normalize_mapping_value(metadata.get("patient_id")),
            }

            subject_name = source_values.get("patient_name") or source_series_uid
            explicit_session_name = None
            matched = not bool(subject_name_map)
            if subject_name_map:
                matched = False
                for source_id in source_ids:
                    for source_candidate in _source_id_candidates(source_values.get(source_id)):
                        key = (source_id, source_candidate)
                        if key in subject_name_map:
                            subject_name = subject_name_map[key]
                            explicit_session_name = session_name_map.get(key)
                            matched = True
                            break
                    if matched:
                        break

                if not matched:
                    unmatched_rows.append({
                        "nifti_file": os.path.basename(f),
                        "series_instance_uid": source_series_uid,
                        "patient_name": source_values.get("patient_name") or "",
                        "patient_id": source_values.get("patient_id") or "",
                        "requested_source_ids": ";".join(source_ids),
                    })
                    continue

            if dataset.has_subject_id(subject_name):
                subject = dataset.get_subject(subject_name)
            else:
                subject = Subject(subject_name)
                dataset.add_subject(subject)

            # session mapping precedence: explicit mapping > date-derived > combined/no-session
            if combine_sessions:
                session_name = ""
            elif explicit_session_name:
                session_name = explicit_session_name
            elif use_session_dates:
                session_name = _session_from_time(time)
            else:
                session_name = ""

            if subject.has_session(session_name):
                session = subject.get_session(session_name)
            else:
                session = Session(session_name)
                subject.add_session(session)

            image = get_image(f, separator, heuristic=heuristic, case_sensitive=case_sensitive)
            if image:
                # Ensure new conversions do not overwrite files in an existing destination session.
                _increment_run_until_unique(image=image,
                                            session=session,
                                            subject_name=subject_name,
                                            session_name=session_name,
                                            bids_directory=bids_directory)
                session.add_image(image)

        if bids_directory:
            print("Writing bids directory: {}".format(bids_directory))
            dataset.set_path(bids_directory)
            if delete_intermediates:
                dataset.update(move=True)
            else:
                dataset.update(move=False)

        if unmatched_rows:
            unmatched_csv = _write_unmatched_source_ids(
                unmatched_rows=unmatched_rows,
                bids_directory=bids_directory,
                input_directory=input_directory,
            )
            raise RuntimeError(
                "Found unmatched conversion rows for subject mapping. See {} and add matching rows before rerun.".format(
                    unmatched_csv
                )
            )
    finally:
        if cleanup_temp_directory and os.path.exists(output_directory):
            shutil.rmtree(output_directory)

    return dataset


def random_hash():
    number = random.getrandbits(128)
    key = "{0:032x}".format(number)
    return key


def random_tmp_directory():
    directory = os.path.join("/tmp", "bidsmanager_" + random_hash())
    os.makedirs(directory)
    return directory


def run_dcm2niix_on_directory(input_directory, output_directory, filename="%t%d%n%p", anonymize=True,
                              verbose=False, directory_depth=9):
    command = ['dcm2niix', "-b", "y", "-ba", "-z", "y", "-d", str(directory_depth),
               "-o", output_directory, "-f", filename, input_directory]
    if anonymize:
        command.insert(4, "y")
    else:
        command.insert(4, "n")
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    output, err = process.communicate()
    if verbose:
        print("dcm2niix output: {}".format(output.decode()))
        print("dcm2niix error: {}".format(err.decode()))
    parse_cmd_output(output)


def parse_cmd_output(cmd_output):
    if "No valid DICOM files were found" in str(cmd_output):
        raise RuntimeError("No valid DICOM files were found")
