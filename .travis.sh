PackageDir=${PWD}
export PYTHONPATH=${PackageDir}:${PYTHONPATH}
cd TEST
nosetests NoseTests/test_dataSet.py
nosetests NoseTests/test_group.py
nosetests NoseTests/test_image.py
nosetests NoseTests/test_reader.py
nosetests NoseTests/test_session.py
nosetests NoseTests/test_subject.py
nosetests NoseTests/test_write.py
codecov --token=69751b3a-1010-436b-86a6-298d9bbf6364
