PackageDir=${PWD}
export PYTHONPATH=${PackageDir}:${PYTHONPATH}
cd TEST
nosetests --with-coverage NoseTests/test_dataSet.py
nosetests --with-coverage NoseTests/test_group.py
nosetests --with-coverage NoseTests/test_image.py
nosetests --with-coverage NoseTests/test_reader.py
nosetests --with-coverage NoseTests/test_session.py
nosetests --with-coverage NoseTests/test_subject.py
nosetests --with-coverage NoseTests/test_write.py
codecov --token=69751b3a-1010-436b-86a6-298d9bbf6364
