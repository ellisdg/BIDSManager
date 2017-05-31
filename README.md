# BIDSManager
[![Build Status](https://travis-ci.org/ellisdg/BIDSManager.svg?branch=master)](https://travis-ci.org/ellisdg/BIDSManager)

Allows users to easily convert, organize, and manage neuroimaging data in Python.

Motivated by issues that have sprung from researchers wanting to store and share neuroimaging data, 
[Gorgolewski, et al.](https://www.nature.com/articles/sdata201644)
proposed a standard organization for storing, sharing, and describing brain imaging datasets, known as the 
[brain imaging data structure (BIDS)](http://bids.neuroimaging.io/). 
Since then, the standard has been gaining traction across neuroimaging researchers. 
Several software tools have been developed to access, process, and convert to and from BIDS data sets. 
Yet no tool has been proposed that allows users to actively organize and manage sets of data for ongoing studies.

BIDSManager serves as an all-in-one tool that allows users looking to quickly access, manage, change, and update their
neuroimaging data sets. Users can quickly add new data to an existing BIDS data set. 
A directory containing DICOMs can be easily sorted by subject and session and then converted to a format that complies 
with BIDS.

## Access an existing BIDS data set
BIDSManager makes it easy to acces data from an existing data set saved to file:
```
from bidsmanager.read import read_dataset
dataset = read_dataset("/path/to/dataset")
```
Image file paths from the data set can then be obtained:
```
t1_image_files = dataset.get_image_paths(modality=“T1w”)
```

## Modify a task name
Here we iterate through all the images in the dataset that had the task name “finger”, change the task name to 
“fingertapping”, and then update the image file paths on file.
```
for image in dataset.get_images(task_name=“finger”):
    image.set_task_name(“fingertapping”)
dataset.update(move=True)
```

## Convert DICOM data
BIDSManager can read in a dicom directory and convert it to a bids directory:
```
from bidsmanager.read.dicom_reader import read_dicom_directory
from bidsmanager.write.dataset_writer import write_dataset
dataset = read_dicom_directory(“/path/to/dicom/directory”)
dataset.set_path(“/path/to/write/bids/directory”)
dataset.update(move=True)
```

## Read CSV File
BIDSManager can also read in a CSV file that contains information on a list of NIFTI file names. BIDS Manager will then
sort those files into a BIDS formatted directory. Take the below information that could be encoded in a CSV file:

| subject | session | modality | file | task |
| ------- | ------- | -------- | ---- | -------- |
| 003 | Visit1 | T1w | /path/to/t1.nii.gz |  |
| 005 | Visit1 | T1w | /path/to/fmri.nii.gz | Finger Tapping |

We can read this CSV file as a data set using BIDSManager and then write the data into BIDS format:
```
from bidsmanager.read import read_csv
dataset = read_csv(“/path/to/csv_file.csv”)
dataset.set_path(“/path/to/write/bids/directory”)
dataset.update()
```