import argparse
import csv
import datetime as dt
import json
import shutil
from pathlib import Path

import pydicom
import pytest
from pydicom.dataset import FileDataset

import convert

pytestmark = pytest.mark.skipif(
    shutil.which("dcm2niix") is None,
    reason="dcm2niix is required for conversion integration tests.",
)


def _write_test_dicom(path: Path, subject: str, series_description: str, when: dt.datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(str(path), {}, preamble=b"\0" * 128, file_meta=file_meta)
    ds.PatientName = subject
    ds.PatientID = subject
    ds.Modality = "MR"
    ds.SeriesDescription = series_description
    ds.StudyDate = when.strftime("%Y%m%d")
    ds.StudyTime = when.strftime("%H%M%S")
    ds.ContentDate = when.strftime("%Y%m%d")
    ds.ContentTime = when.strftime("%H%M%S")
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.Rows = 2
    ds.Columns = 2
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x01\x00\x02\x00\x03\x00\x04\x00"
    ds.save_as(str(path))


# Removed fake dcm2niix stub: tests run the real converter.


@pytest.fixture
def basic_heuristic(tmp_path):
    heuristic = {
        "SeriesDescription": [
            ["T1", {"modality": "T1w"}],
            ["rest", {"modality": "bold", "task": "rest"}],
        ]
    }
    path = tmp_path / "heuristic.json"
    path.write_text(json.dumps(heuristic), encoding="utf-8")
    return path


def _run_main(monkeypatch, input_dir: Path, output_dir: Path, heuristic_file: Path,
              subject_map: Path | None = None,
              use_session_dates: bool | None = None,
              combine_sessions: bool | None = None):
    monkeypatch.setattr(
        convert,
        "parse_args",
        lambda: argparse.Namespace(
            input_dir=str(input_dir),
            output_dir=str(output_dir),
            heuristic=str(heuristic_file),
            subject_map=str(subject_map) if subject_map else None,
            use_session_dates=use_session_dates,
            combine_sessions=combine_sessions,
            verbose=False,
            debug=False,
        ),
    )
    convert.main()


def test_convert_multiple_subjects_into_bids_dataset(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "a" / "scan1.dcm", "SUBJ001", "T1 MPRAGE", dt.datetime(2024, 1, 1, 8, 0, 0))
    _write_test_dicom(input_dir / "b" / "scan1.dcm", "SUBJ002", "T1 MPRAGE", dt.datetime(2024, 1, 1, 9, 0, 0))

    _run_main(monkeypatch, input_dir, out_dir, basic_heuristic)

    assert (out_dir / "sub-SUBJ001").is_dir()
    assert (out_dir / "sub-SUBJ002").is_dir()
    assert list((out_dir / "sub-SUBJ001").rglob("*.nii.gz"))
    assert list((out_dir / "sub-SUBJ002").rglob("*.nii.gz"))


def test_convert_uses_csv_subject_mapping(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_a.dcm", "ALPHA", "T1 MPRAGE", dt.datetime(2024, 1, 2, 8, 0, 0))
    _write_test_dicom(input_dir / "scan_b.dcm", "BETA", "T1 MPRAGE", dt.datetime(2024, 1, 2, 9, 0, 0))

    mapping_csv = tmp_path / "subject_map.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_subject", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_subject": "ALPHA", "bids_subject": "001"})
        writer.writerow({"source_subject": "BETA", "bids_subject": "002"})

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_csv)
    heuristic_path = tmp_path / "heuristic_with_subject_map.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    assert (out_dir / "sub-001").is_dir()
    assert (out_dir / "sub-002").is_dir()


def test_convert_uses_excel_subject_mapping(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_a.dcm", "GAMMA", "T1 MPRAGE", dt.datetime(2024, 1, 3, 8, 0, 0))
    _write_test_dicom(input_dir / "scan_b.dcm", "DELTA", "T1 MPRAGE", dt.datetime(2024, 1, 3, 9, 0, 0))

    mapping_xlsx = tmp_path / "subject_map.xlsx"
    try:
        import pandas as pd

        pd.DataFrame([
            {"source_subject": "GAMMA", "bids_subject": "101"},
            {"source_subject": "DELTA", "bids_subject": "102"},
        ]).to_excel(mapping_xlsx, index=False)
    except Exception:
        # Fallback to CSV-formatted text when Excel writer deps are unavailable.
        mapping_xlsx.write_text(
            "source_subject,bids_subject\nGAMMA,101\nDELTA,102\n",
            encoding="utf-8",
        )

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_xlsx)
    heuristic_path = tmp_path / "heuristic_with_subject_map_excel.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    assert (out_dir / "sub-101").is_dir()
    assert (out_dir / "sub-102").is_dir()


def test_convert_assigns_sessions_by_date_and_can_combine(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "day1" / "scan.dcm", "SUBJ010", "T1 MPRAGE", dt.datetime(2024, 3, 1, 10, 0, 0))
    _write_test_dicom(input_dir / "day2" / "scan.dcm", "SUBJ010", "T1 MPRAGE", dt.datetime(2024, 3, 5, 10, 0, 0))

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["use_session_dates"] = True
    heuristic["combine_sessions"] = False
    heuristic_path = tmp_path / "heuristic_with_sessions.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    assert (out_dir / "sub-SUBJ010" / "ses-20240301").is_dir()
    assert (out_dir / "sub-SUBJ010" / "ses-20240305").is_dir()


def test_convert_merges_into_preexisting_bids_directory(tmp_path, monkeypatch, basic_heuristic):
    first_input = tmp_path / "dicoms_first"
    second_input = tmp_path / "dicoms_second"
    out_dir = tmp_path / "bids"

    _write_test_dicom(first_input / "scan1.dcm", "SUBJ100", "T1 MPRAGE", dt.datetime(2024, 4, 1, 7, 30, 0))
    _write_test_dicom(second_input / "scan1.dcm", "SUBJ200", "T1 MPRAGE", dt.datetime(2024, 4, 2, 7, 30, 0))

    _run_main(monkeypatch, first_input, out_dir, basic_heuristic)
    _run_main(monkeypatch, second_input, out_dir, basic_heuristic)

    assert (out_dir / "sub-SUBJ100").is_dir()
    assert (out_dir / "sub-SUBJ200").is_dir()
    assert list((out_dir / "sub-SUBJ100").rglob("*.nii.gz"))
    assert list((out_dir / "sub-SUBJ200").rglob("*.nii.gz"))


def test_convert_merges_new_dicoms_into_preexisting_session_by_date(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    existing_session_dir = out_dir / "sub-SUBJ300" / "ses-20240506" / "anat"
    existing_session_dir.mkdir(parents=True, exist_ok=True)
    (existing_session_dir / "sub-SUBJ300_ses-20240506_T1w.nii.gz").write_bytes(b"existing")

    _write_test_dicom(input_dir / "scan1.dcm", "SUBJ300", "T1 MPRAGE", dt.datetime(2024, 5, 6, 12, 0, 0))

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["use_session_dates"] = True
    heuristic_path = tmp_path / "heuristic_use_session_dates.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    session_files = list((out_dir / "sub-SUBJ300" / "ses-20240506").rglob("*.nii.gz"))
    assert len(session_files) >= 2


def test_convert_merges_new_dicoms_into_preexisting_session_by_explicit_mapping(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    existing_session_dir = out_dir / "sub-777" / "ses-baseline" / "anat"
    existing_session_dir.mkdir(parents=True, exist_ok=True)
    (existing_session_dir / "sub-777_ses-baseline_T1w.nii.gz").write_bytes(b"existing")

    _write_test_dicom(input_dir / "scan1.dcm", "RAW777", "T1 MPRAGE", dt.datetime(2024, 6, 1, 9, 0, 0))

    mapping_csv = tmp_path / "subject_session_map.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_subject", "bids_subject", "session_id"])
        writer.writeheader()
        writer.writerow({"source_subject": "RAW777", "bids_subject": "777", "session_id": "baseline"})

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_csv)
    heuristic_path = tmp_path / "heuristic_with_subject_session_map.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    session_files = list((out_dir / "sub-777" / "ses-baseline").rglob("*.nii.gz"))
    assert len(session_files) >= 2


def test_collision_handling_assigns_next_run_number(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    existing_anat_dir = out_dir / "sub-COLLIDE" / "ses-20240701" / "anat"
    existing_anat_dir.mkdir(parents=True, exist_ok=True)
    existing_file = existing_anat_dir / "sub-COLLIDE_ses-20240701_run-01_T1w.nii.gz"
    existing_file.write_bytes(b"existing")

    _write_test_dicom(input_dir / "scan1.dcm", "COLLIDE", "T1 MPRAGE", dt.datetime(2024, 7, 1, 11, 0, 0))

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["use_session_dates"] = True
    heuristic["combine_sessions"] = False
    heuristic_path = tmp_path / "heuristic_collision.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path)

    assert existing_file.exists()
    assert (existing_anat_dir / "sub-COLLIDE_ses-20240701_run-02_T1w.nii.gz").exists()


def test_convert_uses_cli_subject_map_argument(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_a.dcm", "EPSILON", "T1 MPRAGE", dt.datetime(2024, 1, 4, 8, 0, 0))

    mapping_csv = tmp_path / "subject_map_cli.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_subject", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_subject": "EPSILON", "bids_subject": "201"})

    _run_main(monkeypatch, input_dir, out_dir, basic_heuristic, subject_map=mapping_csv)

    assert (out_dir / "sub-201").is_dir()
