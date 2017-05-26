PackageDir=${PWD}
export PYTHONPATH=${PackageDir}:${PYTHONPATH}
cd TEST
nosetests --with-coverage --exclude=NoseTests/test_dicomreader.py
codecov --token=69751b3a-1010-436b-86a6-298d9bbf6364
