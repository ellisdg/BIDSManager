#!/usr/bin/env python3
import argparse
import json
import os


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
    return parser.parse_args()



def main():
    from bidsmanager.read.dicom_reader import convert_dicom_directory
    args = parse_args()
    # Load heuristic from JSON file
    with open(args.heuristic, 'r') as f:
        heuristic = json.load(f)
    convert_dicom_directory(input_directory=os.path.abspath(args.input_dir),
                             heuristic=heuristic,
                             anonymize=True,
                            bids_directory=os.path.abspath(args.output_dir),
                             delete_intermediates=True)


if __name__ == "__main__":
    main()
