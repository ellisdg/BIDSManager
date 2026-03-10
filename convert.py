#!/usr/bin/env python3
import argparse
import json
import os
import glob


def parse_args():
    parser = argparse.ArgumentParser(description="Convert DICOM files to BIDS format.")
    parser.add_argument("input_dir", type=str, help="Input directory containing DICOM files.")
    parser.add_argument("output_dir", type=str, help="Output directory for BIDS formatted files.")
    parser.add_argument(
        "--heuristic",
        type=str,
        help="Path to the heuristic JSON file.",
        required=True
    )
    parser.add_argument(
        "--subject-map",
        type=str,
        default=None,
        help="Optional CSV/XLS/XLSX mapping file for source_subject -> bids_subject/session_id.",
    )
    parser.add_argument(
        "--use-session-dates",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Use acquisition dates for session names (ses-YYYYMMDD).",
    )
    parser.add_argument(
        "--combine-sessions",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Combine all scans into a single no-session directory per subject.",
    )
    parser.add_argument(
        "--source-id-from-mrn",
        action="store_true",
        help="Use DICOM PatientID (MRN) as the source identifier for subject mapping.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    return parser.parse_args()


def search_for_dicom_files(input_dir, output_file, give_up_after=1000):
    """
    Search for DICOM files in the input directory and its subdirectories.
    :param input_dir:
    :param output_file: output csv file to save the results
    :param give_up_after: number of files to check before giving up if no valid DICOM files are found
    :return:
    """
    import pydicom
    import pydicom.errors

    print("Searching for DICOM files in directory: {}".format(input_dir))
    all_files = glob.glob(os.path.join(input_dir, "**", "*"), recursive=True)
    print("Found {} files and directories.".format(len(all_files)))
    thrown_errors = dict()
    dicom_files = []
    valid_count = 0
    print("Checking for valid DICOM files...")
    for file in all_files:
        if os.path.isfile(file):
            try:
                dicom = pydicom.dcmread(file, stop_before_pixels=True)
                valid_count += 1
            except pydicom.errors.InvalidDicomError as e:
                dicom_files.append([file, e])
                if e not in thrown_errors:
                    thrown_errors[e] = 1
                else:
                    thrown_errors[e] += 1
            except IOError as e:
                dicom_files.append([file, e])
                if e not in thrown_errors:
                    thrown_errors[e] = 1
                else:
                    thrown_errors[e] += 1
            except Exception as e:
                dicom_files.append([file, e])
                if e not in thrown_errors:
                    thrown_errors[e] = 1
                else:
                    thrown_errors[e] += 1
            if len(dicom_files) >= give_up_after and valid_count == 0:
                print("Could not find any valid DICOMS after checking {} files. Stopping.".format(give_up_after))
                # force read the file to see what tags are present
                print("Force reading file and checking DICOM tags: {}".format(file))
                dicom = pydicom.dcmread(file, force=True)
                # print the tags
                print("DICOM tag keys found in file: {}".format([elem.keyword or elem.name for elem in dicom]))
                break

    print("Found {} valid DICOM files.".format(valid_count))
    print("Found {} invalid DICOM files.".format(len(dicom_files)))
    if len(thrown_errors) > 0:
        print("Found {} errors while reading DICOM files.".format(len(thrown_errors)))
        for error, count in thrown_errors.items():
            print("\tError: {} - Count: {}".format(error, count))
    print("Writing DICOM validity results to {}".format(output_file))
    with open(output_file, "w") as f:
        for file, is_valid in dicom_files:
            f.write("{},{}\n".format(file, is_valid))


def main():
    from bidsmanager.read.dicom_reader import convert_dicom_directory
    args = parse_args()
    # Load heuristic from JSON file
    with open(args.heuristic, 'r') as f:
        heuristic = json.load(f)

    # CLI args override heuristic values when provided.
    subject_map = args.subject_map if args.subject_map else heuristic.get("subject_map")
    # Backward compatibility for existing heuristic files.
    if not subject_map:
        subject_map = heuristic.get("subject_map_csv") or heuristic.get("subject_map_excel")

    use_session_dates = args.use_session_dates
    if use_session_dates is None:
        use_session_dates = heuristic.get("use_session_dates", False)

    combine_sessions = args.combine_sessions
    if combine_sessions is None:
        combine_sessions = heuristic.get("combine_sessions", False)

    source_id_from_mrn = args.source_id_from_mrn or heuristic.get("source_id_from_mrn", False)

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    verbose = args.verbose
    if args.debug:
        verbose = True
        # Create a CSV file to store the DICOM files found
        output_file = os.path.join(output_dir, "source", "dicom_files.csv")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        search_for_dicom_files(input_dir, output_file)
    convert_dicom_directory(input_directory=input_dir,
                            heuristic=heuristic,
                            anonymize=True,
                            bids_directory=output_dir,
                            delete_intermediates=True,
                            verbose=verbose,
                            use_session_dates=use_session_dates,
                            combine_sessions=combine_sessions,
                            subject_map=subject_map,
                            source_id_from_mrn=source_id_from_mrn)


if __name__ == "__main__":
    main()
