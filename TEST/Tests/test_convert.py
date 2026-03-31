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
from bidsmanager.read import dicom_reader

pytestmark = pytest.mark.skipif(
    shutil.which("dcm2niix") is None,
    reason="dcm2niix is required for conversion integration tests.",
)


def _write_test_dicom(path: Path, subject: str, series_description: str, when: dt.datetime,
                      mrn: str | None = None, series_number: int | None = None,
                      series_instance_uid: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(str(path), {}, preamble=b"\0" * 128, file_meta=file_meta)
    ds.PatientName = subject
    ds.PatientID = mrn if mrn is not None else subject
    ds.Modality = "MR"
    ds.SeriesDescription = series_description
    if series_number is not None:
        ds.SeriesNumber = series_number
    ds.StudyDate = when.strftime("%Y%m%d")
    ds.StudyTime = when.strftime("%H%M%S")
    ds.ContentDate = when.strftime("%Y%m%d")
    ds.ContentTime = when.strftime("%H%M%S")
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = series_instance_uid if series_instance_uid is not None else pydicom.uid.generate_uid()
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


def test_parse_image_keys_can_skip_derivative_series_numbers():
    heuristic = {
        "SeriesDescription": [["T1", {"modality": "T1w"}]],
        "SeriesNumber": [[r"0[2-9]$", None]],
    }

    for series_number in ("102", "202", "303", "1207", "1102"):
        assert dicom_reader.parse_image_keys(
            in_file=f"sub-001---20240101080000---T1 MPRAGE---MPRAGE---{series_number}---.nii.gz",
            description="T1 MPRAGE",
            series_number=series_number,
            heuristic=heuristic,
        ) is None


def test_parse_image_keys_keeps_non_derivative_series_numbers():
    heuristic = {
        "SeriesDescription": [["T1", {"modality": "T1w"}]],
        "SeriesNumber": [[r"0[2-9]$", None]],
    }

    assert dicom_reader.parse_image_keys(
        in_file="sub-001---20240101080000---T1 MPRAGE---MPRAGE---101---.nii.gz",
        description="T1 MPRAGE",
        series_number="101",
        heuristic=heuristic,
    ) == {"modality": "T1w"}


def test_convert_excludes_derivative_series_by_series_number(tmp_path, monkeypatch):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(
        input_dir / "scan_101.dcm",
        "SUBJ900",
        "T1 MPRAGE",
        dt.datetime(2024, 7, 1, 8, 0, 0),
        series_number=101,
    )
    _write_test_dicom(
        input_dir / "scan_202.dcm",
        "SUBJ900",
        "T1 MPRAGE",
        dt.datetime(2024, 7, 1, 8, 5, 0),
        series_number=202,
    )

    heuristic = {
        "SeriesDescription": [["T1", {"modality": "T1w"}]],
        "SeriesNumber": [[r"0[2-9]$", None]],
    }
    heuristic_path = tmp_path / "heuristic_series_number.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    output_dir = tmp_path / "dcm2niix_out"

    def _fake_run_dcm2niix_on_directory(input_directory, output_directory, **kwargs):
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        for dicom_path in sorted(Path(input_directory).rglob("*.dcm")):
            ds = pydicom.dcmread(str(dicom_path), stop_before_pixels=True)
            series_uid = str(ds.SeriesInstanceUID)
            series_number = str(ds.SeriesNumber)
            (Path(output_directory) / f"{series_uid}---{ds.ContentTime}---{ds.SeriesDescription}---MPRAGE---{series_number}---.nii.gz").write_bytes(b"")

    monkeypatch.setattr(dicom_reader, "random_tmp_directory", lambda: str(output_dir))
    monkeypatch.setattr(dicom_reader, "run_dcm2niix_on_directory", _fake_run_dcm2niix_on_directory)

    dataset = dicom_reader.convert_dicom_directory(
        input_directory=str(input_dir),
        heuristic=heuristic,
        bids_directory=str(out_dir),
        delete_intermediates=True,
        cleanup_temp_directory=True,
    )

    assert dataset.has_subject_id("SUBJ900")
    assert len(dataset.get_images(modality="T1w")) == 1
    assert list(out_dir.rglob("*.nii.gz"))
    assert not any(path.name.endswith("---202---.nii.gz") for path in out_dir.rglob("*.nii.gz"))


def _run_main(monkeypatch, input_dir: Path, output_dir: Path, heuristic_file: Path,
              subject_map: Path | None = None,
              use_session_dates: bool | None = None,
              combine_sessions: bool | None = None,
              source_ids: list[str] | None = None,
              debug: bool = False):
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
            source_id=source_ids,
            no_anonymize=False,
            verbose=False,
            debug=debug,
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


def test_convert_omits_run_number_for_single_image(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan1.dcm", "SUBJ001", "T1 MPRAGE", dt.datetime(2024, 1, 1, 8, 0, 0))

    _run_main(monkeypatch, input_dir, out_dir, basic_heuristic)

    expected = out_dir / "sub-SUBJ001" / "anat" / "sub-SUBJ001_T1w.nii.gz"
    assert expected.exists()
    assert not any("run-" in path.name for path in (out_dir / "sub-SUBJ001").rglob("*.nii.gz"))


def test_convert_uses_csv_subject_mapping(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_a.dcm", "ALPHA", "T1 MPRAGE", dt.datetime(2024, 1, 2, 8, 0, 0))
    _write_test_dicom(input_dir / "scan_b.dcm", "BETA", "T1 MPRAGE", dt.datetime(2024, 1, 2, 9, 0, 0))

    mapping_csv = tmp_path / "subject_map.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_patient_name", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_patient_name": "ALPHA", "bids_subject": "001"})
        writer.writerow({"source_patient_name": "BETA", "bids_subject": "002"})

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_csv)
    heuristic_path = tmp_path / "heuristic_with_subject_map.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path, source_ids=["patient_name"])

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
            {"source_patient_name": "GAMMA", "bids_subject": "101"},
            {"source_patient_name": "DELTA", "bids_subject": "102"},
        ]).to_excel(mapping_xlsx, index=False)
    except Exception:
        # Fallback to CSV-formatted text when Excel writer deps are unavailable.
        mapping_xlsx.write_text(
            "source_patient_name,bids_subject\nGAMMA,101\nDELTA,102\n",
            encoding="utf-8",
        )

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_xlsx)
    heuristic_path = tmp_path / "heuristic_with_subject_map_excel.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path, source_ids=["patient_name"])

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
        writer = csv.DictWriter(f, fieldnames=["source_patient_name", "bids_subject", "session_id"])
        writer.writeheader()
        writer.writerow({"source_patient_name": "RAW777", "bids_subject": "777", "session_id": "baseline"})

    heuristic = json.loads(basic_heuristic.read_text(encoding="utf-8"))
    heuristic["subject_map"] = str(mapping_csv)
    heuristic_path = tmp_path / "heuristic_with_subject_session_map.json"
    heuristic_path.write_text(json.dumps(heuristic), encoding="utf-8")

    _run_main(monkeypatch, input_dir, out_dir, heuristic_path, source_ids=["patient_name"])

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
        writer = csv.DictWriter(f, fieldnames=["source_patient_name", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_patient_name": "EPSILON", "bids_subject": "201"})

    _run_main(
        monkeypatch,
        input_dir,
        out_dir,
        basic_heuristic,
        subject_map=mapping_csv,
        source_ids=["patient_name"],
    )

    assert (out_dir / "sub-201").is_dir()


def test_convert_uses_patient_id_subject_mapping(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(
        input_dir / "scan_mrn1.dcm",
        "PATIENT_A",
        "T1 MPRAGE",
        dt.datetime(2024, 1, 5, 8, 0, 0),
        mrn="MRN1001",
    )
    _write_test_dicom(
        input_dir / "scan_mrn2.dcm",
        "PATIENT_B",
        "T1 MPRAGE",
        dt.datetime(2024, 1, 5, 9, 0, 0),
        mrn="001002",
    )

    mapping_csv = tmp_path / "subject_map_mrn.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_patient_id", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_patient_id": "MRN1001", "bids_subject": "301"})
        writer.writerow({"source_patient_id": "1002", "bids_subject": "302"})

    _run_main(
        monkeypatch,
        input_dir,
        out_dir,
        basic_heuristic,
        subject_map=mapping_csv,
        source_ids=["patient_id"],
    )

    assert (out_dir / "sub-301").is_dir()
    assert (out_dir / "sub-302").is_dir()


def test_convert_requires_source_ids_when_using_subject_map(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_a.dcm", "NOIDS", "T1 MPRAGE", dt.datetime(2024, 1, 6, 8, 0, 0))

    mapping_csv = tmp_path / "subject_map_missing_ids.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_patient_name", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_patient_name": "NOIDS", "bids_subject": "901"})

    with pytest.raises(ValueError, match="source-id"):
        _run_main(monkeypatch, input_dir, out_dir, basic_heuristic, subject_map=mapping_csv)


def test_convert_fails_after_writing_matched_rows_and_dumps_unmatched(tmp_path, monkeypatch, basic_heuristic, capsys):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan_match.dcm", "MATCHED", "T1 MPRAGE", dt.datetime(2024, 1, 7, 8, 0, 0))
    _write_test_dicom(input_dir / "scan_miss.dcm", "MISSING", "T1 MPRAGE", dt.datetime(2024, 1, 7, 9, 0, 0))

    mapping_csv = tmp_path / "subject_map_partial.csv"
    with mapping_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_patient_name", "bids_subject"])
        writer.writeheader()
        writer.writerow({"source_patient_name": "MATCHED", "bids_subject": "777"})

    with pytest.raises(RuntimeError, match="unmatched"):
        _run_main(
            monkeypatch,
            input_dir,
            out_dir,
            basic_heuristic,
            subject_map=mapping_csv,
            source_ids=["patient_name"],
        )

    assert (out_dir / "sub-777").is_dir()
    unmatched_csv = out_dir / "source" / "unmatched_source_ids.csv"
    assert unmatched_csv.exists()
    csv_text = unmatched_csv.read_text(encoding="utf-8")
    assert "MISSING" in csv_text

    stdout = capsys.readouterr().out
    assert "MISSING" in stdout


def test_main_enables_temp_cleanup_by_default(tmp_path, monkeypatch, basic_heuristic):
    captured = {}

    def _fake_convert_dicom_directory(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("bidsmanager.read.dicom_reader.convert_dicom_directory", _fake_convert_dicom_directory)

    _run_main(monkeypatch, tmp_path / "dicoms", tmp_path / "bids", basic_heuristic, debug=False)

    assert captured["cleanup_temp_directory"] is True


def test_main_disables_temp_cleanup_in_debug_mode(tmp_path, monkeypatch, basic_heuristic):
    captured = {}

    def _fake_convert_dicom_directory(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("bidsmanager.read.dicom_reader.convert_dicom_directory", _fake_convert_dicom_directory)

    _run_main(monkeypatch, tmp_path / "dicoms", tmp_path / "bids", basic_heuristic, debug=True)

    assert captured["cleanup_temp_directory"] is False


def test_convert_dicom_directory_cleans_temp_directory_by_default(tmp_path, monkeypatch):
    temp_dir = tmp_path / "tmp_dcm2niix"

    def _fake_random_tmp_directory():
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir)

    monkeypatch.setattr(dicom_reader, "random_tmp_directory", _fake_random_tmp_directory)
    monkeypatch.setattr(dicom_reader, "run_dcm2niix_on_directory", lambda *args, **kwargs: None)

    dicom_reader.convert_dicom_directory(
        input_directory=str(tmp_path / "dicoms"),
        heuristic={"SeriesDescription": [["T1", {"modality": "T1w"}]]},
    )

    assert not temp_dir.exists()


def test_convert_dicom_directory_keeps_temp_directory_when_requested(tmp_path, monkeypatch):
    temp_dir = tmp_path / "tmp_dcm2niix_keep"

    def _fake_random_tmp_directory():
        temp_dir.mkdir(parents=True, exist_ok=True)
        return str(temp_dir)

    monkeypatch.setattr(dicom_reader, "random_tmp_directory", _fake_random_tmp_directory)
    monkeypatch.setattr(dicom_reader, "run_dcm2niix_on_directory", lambda *args, **kwargs: None)

    dicom_reader.convert_dicom_directory(
        input_directory=str(tmp_path / "dicoms"),
        heuristic={"SeriesDescription": [["T1", {"modality": "T1w"}]]},
        cleanup_temp_directory=False,
    )

    assert temp_dir.exists()


def test_parse_acquisition_time_handles_valid_missing_and_invalid_tokens():
    assert dicom_reader._parse_acquisition_time("20240101123456") is not None
    assert dicom_reader._parse_acquisition_time("") is None
    assert dicom_reader._parse_acquisition_time("not-a-time") is None


def test_convert_handles_missing_acquisition_time_without_breaking(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(input_dir / "scan1.dcm", "SUBJ001", "T1 MPRAGE", dt.datetime(2024, 1, 1, 8, 0, 0), series_instance_uid="1.1.1")
    _write_test_dicom(input_dir / "scan2.dcm", "SUBJ001", "T1 MPRAGE", dt.datetime(2024, 1, 1, 9, 0, 0), series_instance_uid="2.2.2")

    output_dir = tmp_path / "dcm2niix_out"

    def _fake_run_dcm2niix_on_directory(input_directory, output_directory, **kwargs):
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        (Path(output_directory) / "1.1.1---20240101080000---T1 MPRAGE---MPRAGE---101---.nii.gz").write_bytes(b"")
        (Path(output_directory) / "2.2.2------T1 MPRAGE---MPRAGE---101---.nii.gz").write_bytes(b"")

    monkeypatch.setattr(dicom_reader, "random_tmp_directory", lambda: str(output_dir))
    monkeypatch.setattr(dicom_reader, "run_dcm2niix_on_directory", _fake_run_dcm2niix_on_directory)

    dataset = dicom_reader.convert_dicom_directory(
        input_directory=str(input_dir),
        heuristic=json.loads(basic_heuristic.read_text(encoding="utf-8")),
        bids_directory=str(out_dir),
        delete_intermediates=True,
        cleanup_temp_directory=True,
    )

    images = dataset.get_images(modality="T1w")
    assert len(images) == 2
    assert {image.get_run_number() for image in images} == {1, 2}


def test_convert_orders_runs_by_acquisition_time(tmp_path, monkeypatch, basic_heuristic):
    input_dir = tmp_path / "dicoms"
    out_dir = tmp_path / "bids"

    _write_test_dicom(
        input_dir / "scan1.dcm",
        "SUBJ001",
        "T1 MPRAGE",
        dt.datetime(2024, 1, 1, 8, 0, 0),
        series_instance_uid="2.2.2",
    )
    _write_test_dicom(
        input_dir / "scan2.dcm",
        "SUBJ001",
        "T1 MPRAGE",
        dt.datetime(2024, 1, 1, 9, 0, 0),
        series_instance_uid="1.1.1",
    )

    output_dir = tmp_path / "dcm2niix_out"

    def _fake_run_dcm2niix_on_directory(input_directory, output_directory, **kwargs):
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        (Path(output_directory) / "1.1.1---20240101090000---T1 MPRAGE---MPRAGE---101---.nii.gz").write_bytes(b"")
        (Path(output_directory) / "2.2.2---20240101080000---T1 MPRAGE---MPRAGE---101---.nii.gz").write_bytes(b"")

    monkeypatch.setattr(dicom_reader, "random_tmp_directory", lambda: str(output_dir))
    monkeypatch.setattr(dicom_reader, "run_dcm2niix_on_directory", _fake_run_dcm2niix_on_directory)

    dataset = dicom_reader.convert_dicom_directory(
        input_directory=str(input_dir),
        heuristic=json.loads(basic_heuristic.read_text(encoding="utf-8")),
        bids_directory=str(out_dir),
        delete_intermediates=True,
        cleanup_temp_directory=True,
    )

    images = dataset.get_images(modality="T1w")
    assert len(images) == 2
    images_by_time = {image.get_metadata("AcquisitionTime"): image for image in images}
    assert images_by_time[dt.datetime(2024, 1, 1, 8, 0, 0)].get_run_number() == 1
    assert images_by_time[dt.datetime(2024, 1, 1, 9, 0, 0)].get_run_number() == 2


