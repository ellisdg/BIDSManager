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
bash <(curl -s https://codecov.io/bash)
