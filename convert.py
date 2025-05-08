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
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    return parser.parse_args()


def search_for_dicom_files(input_dir, output_file):
    """
    Search for DICOM files in the input directory and its subdirectories.
    :param input_dir:
    :param output_file: output csv file to save the results
    :return:
    """
    import pydicom
    import pydicom.errors

    print("Searching for DICOM files in directory: {}".format(input_dir))
    all_files = glob.glob(os.path.join(input_dir, "**", "*"), recursive=True)
    print("Found {} files and directories.".format(len(all_files)))
    dicom_files = []
    valid_count = 0
    print("Checking for valid DICOM files...")
    for file in all_files:
        if os.path.isfile(file):
            try:
                dicom = pydicom.dcmread(file, stop_before_pixels=True)
                dicom_files.append([file, True])
                valid_count += 1
            except pydicom.errors.InvalidDicomError:
                dicom_files.append([file, False])
    print("Found {} valid DICOM files.".format(valid_count))
    print("Found {} invalid DICOM files.".format(len(dicom_files) - valid_count))
    print("Writing results to {}".format(output_file))
    with open(output_file, "w") as f:
        for file, is_valid in dicom_files:
            f.write("{},{}\n".format(file, is_valid))


def main():
    from bidsmanager.read.dicom_reader import convert_dicom_directory
    args = parse_args()
    # Load heuristic from JSON file
    with open(args.heuristic, 'r') as f:
        heuristic = json.load(f)
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    if args.debug:
        # Create a CSV file to store the DICOM files found
        output_file = os.path.join(output_dir, "source", "dicom_files.csv")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        search_for_dicom_files(input_dir, output_file)
    convert_dicom_directory(input_directory=input_dir,
                            heuristic=heuristic,
                            anonymize=True,
                            bids_directory=output_dir,
                            delete_intermediates=True,
                            verbose=args.verbose)


if __name__ == "__main__":
    main()
