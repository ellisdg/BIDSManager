# BIDSManager
[![Build Status](https://travis-ci.org/ellisdg/BIDSManager.svg?branch=master)](https://travis-ci.org/ellisdg/BIDSManager)
[![codecov](https://codecov.io/gh/ellisdg/BIDSManager/branch/master/graph/badge.svg)](https://codecov.io/gh/ellisdg/BIDSManager)

BIDSManager helps you convert, organize, and manage neuroimaging data in Python.

It is motivated by the BIDS standard described by
[Gorgolewski et al.](https://www.nature.com/articles/sdata201644), and is designed for active studies where
new data is continuously added and curated.

## Convert DICOM to BIDS with `convert.py`

For most users, the main entry point is `convert.py`.

### Basic usage

```bash
python convert.py /path/to/dicom_dir /path/to/bids_out --heuristic /path/to/heuristic.json
```

### Command-line options

- `--heuristic`: required JSON heuristic file describing how `SeriesDescription` maps to BIDS entities.
- `--subject-map`: optional mapping file (`.csv`, `.xls`, or `.xlsx`) for subject/session mapping.
- `--use-session-dates` / `--no-use-session-dates`: optionally derive session names from acquisition dates.
- `--combine-sessions` / `--no-combine-sessions`: optionally place all scans for a subject into one no-session folder.
- `--source-id-from-mrn`: use DICOM `PatientID` (MRN) instead of `PatientName` for source ID matching.
- `--no-anonymize`: disable anonymization passed to dcm2niix.
- `--verbose`: show dcm2niix output.
- `--debug`: run a DICOM validity scan, write diagnostics to `output_dir/source/dicom_files.csv`, and keep the temporary dcm2niix directory for inspection.

Example with mapping and date-based sessions:

```bash
python convert.py /path/to/dicoms /path/to/bids \
  --heuristic /path/to/heuristic.json \
  --subject-map /path/to/subject_map.csv \
  --use-session-dates \
  --no-combine-sessions
```

### Subject map format

`--subject-map` (or `"subject_map"` in heuristic JSON) can include these columns:

- `source_subject` (required for mapping rows)
- `bids_subject` (optional; defaults to source subject if omitted)
- `session_id` (optional; when present, overrides date-derived session naming)

Example CSV:

```csv
source_subject,bids_subject,session_id
RAW001,001,baseline
RAW002,002,followup
```

### Heuristic example

```json
{
  "SeriesDescription": [
    ["T1", {"modality": "T1w"}],
    ["rest", {"modality": "bold", "task": "rest"}]
  ],
  "subject_map": "/path/to/subject_map.csv",
  "use_session_dates": true,
  "combine_sessions": false
}
```

Notes:

- CLI values override heuristic values when both are provided.
- `subject_map` is selected by file extension (`.csv`, `.xls`, `.xlsx`).
- Temporary dcm2niix output is deleted by default after conversion; use `--debug` to keep it.

## Access an existing BIDS dataset

```python
from bidsmanager.read import read_dataset

dataset = read_dataset("/path/to/dataset")
t1_image_files = dataset.get_image_paths(modality="T1w")
```

## Modify task names

```python
for image in dataset.get_images(task="finger"):
    image.set_task_name("fingertapping")
dataset.update(move=True)
```

## Build a BIDS dataset from CSV metadata

BIDSManager can read a CSV describing NIfTI files and then write a BIDS directory.

Example table:

| subject | session | modality | file | task |
| ------- | ------- | -------- | ---- | ---- |
| 003 | Visit1 | T1w | /path/to/t1.nii.gz | |
| 005 | Visit1 | bold | /path/to/fmri.nii.gz | Finger Tapping |

```python
from bidsmanager.read import read_csv

dataset = read_csv("/path/to/csv_file.csv")
dataset.set_path("/path/to/write/bids/directory")
dataset.update()
```
