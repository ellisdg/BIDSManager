# BIDSManager
[![Build Status](https://travis-ci.org/ellisdg/bids.svg?branch=master)](https://travis-ci.org/ellisdg/bids)

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