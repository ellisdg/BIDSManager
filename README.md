# BIDSManager
[![Build Status](https://travis-ci.org/ellisdg/bids.svg?branch=master)](https://travis-ci.org/ellisdg/bids)

Access, write and modify BIDS data sets with ease!

The [Brain Imaging Data Structure (BIDS)](http://bids.neuroimaging.io/) is a "simple and inuitive way to organize and 
describe your neruoimaging and behavioral data." The BIDS format creates a standardized way to store and share data 
sets.
However, formatting existing neuroimaging data sets into the BIDS structure can be time consuming.

This project is designed to allow users to quickly read, write and modify BIDS data sets in Python.

## Read BIDS Data Set
Read a data set that is already in BIDS format:
```
from bidsmanager.read import read_dataset
dataset = read_dataset("/path/to/dataset")
```
Now that you have a Python interface to the data set, you can also get_field the interfaces for specific subjects, sessions or
groups:
```
subject_01 = dataset.get_subject("01")
session_retest = subject_01.get_session("retest")
group_func = session.get_group("func")
```
You can also get_field the image paths for the entire data set:
```
all_t1w_file_paths = dataset.get_image_paths(modality="T1w")
```
...or for a particular subject:
```
t1w_01_file_paths = subject_01.get_image_paths(modality="T1w")
```
A single line equivelant would be as follows:
```
t1w_01_file_paths = dataset.get_subject("01").get_image_paths(modality="T1w")
```
## Write BIDS Data Set