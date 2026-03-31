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
- `--source-id`: repeatable source identifier used for subject mapping. Supported values: `patient_name`, `patient_id`.
- `--no-anonymize`: disable anonymization passed to dcm2niix.
- `--verbose`: show dcm2niix output.
- `--debug`: run a DICOM validity scan, write diagnostics to `output_dir/source/dicom_files.csv`, and keep the temporary dcm2niix directory for inspection.

Example with mapping and date-based sessions:

```bash
python convert.py /path/to/dicoms /path/to/bids \
  --heuristic /path/to/heuristic.json \
  --subject-map /path/to/subject_map.csv \
  --source-id patient_id \
  --source-id patient_name \
  --use-session-dates \
  --no-combine-sessions
```

### Subject map format

`--subject-map` (or `"subject_map"` in heuristic JSON) can include these columns:

- `source_patient_name` (used when `--source-id patient_name`)
- `source_patient_id` (used when `--source-id patient_id`)
- `bids_subject` (optional; defaults to source subject if omitted)
- `session_id` (optional; when present, overrides date-derived session naming)

### Identifier semantics (important)

- `patient_id` is read from DICOM tag `PatientID` (`0010,0020`).
- This is the same conceptual field as dcm2niix `%i`, but it is **site-defined** and is **not guaranteed** to be a medical record number (MRN).
- If your site stores accession, research IDs, or internal aliases in `PatientID`, map against those exact values.
- `patient_name` is read from DICOM tag `PatientName` (`0010,0010`) and matched by exact string value (after trimming surrounding whitespace).

### Name matching rules for `patient_name`

- Matching is currently exact and case-sensitive.
- BIDSManager does **not** split, normalize, or reorder person-name components.
- DICOM names are often encoded like `FAMILY^GIVEN^MIDDLE^PREFIX^SUFFIX`.
- Example: if the DICOM value is `JOHN^SMITH^E`, the subject map must use `JOHN^SMITH^E` to match.
- A map value like `John`, `Smith`, or `John Smith` will not match `JOHN^SMITH^E`.

Example CSV:

```csv
source_patient_id,source_patient_name,bids_subject,session_id
000123,RAW001,001,baseline
000456,RAW002,002,followup
```

Example with DICOM person-name formatting:

```csv
source_patient_name,bids_subject
JOHN^SMITH^E,010
DOE^JANE,011
```

### Heuristic example

```json
{
  "SeriesDescription": [
    ["T1", {"modality": "T1w"}],
    ["rest", {"modality": "bold", "task": "rest"}]
  ],
  "SeriesNumber": [
    ["0[2-9]$", null]
  ],
  "subject_map": "/path/to/subject_map.csv",
  "source_id": ["patient_id", "patient_name"],
  "use_session_dates": true,
  "combine_sessions": false
}
```

Notes:

- CLI values override heuristic values when both are provided.
- `subject_map` is selected by file extension (`.csv`, `.xls`, `.xlsx`).
- When using `subject_map`, provide one or more `--source-id` values (or `"source_id"` in heuristic JSON).
- Add `"SeriesNumber"` entries to skip derivative acquisitions by series number; use `null` as the value to exclude matching files. For example, `"0[2-9]$"` excludes `102`, `203`, `307`, `1209`, and any other series number ending in `02` through `09`.
- If your intent is MRN-based matching, first verify that your MRN is actually stored in DICOM `PatientID` (`0010,0020`).
- If any converted scans are unmatched, matched rows are still written, then conversion fails and writes full details to `output_dir/source/unmatched_source_ids.csv`.
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
