FROM ubuntu:noble

# Install Dependencies
RUN apt-get update && apt-get upgrade -y && \
	apt-get install -y build-essential pkg-config cmake git pigz && \
	apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

# Get dcm2niix from github and compile
RUN cd /tmp && \
	git clone https://github.com/rordenlab/dcm2niix.git && \
	cd dcm2niix && mkdir build && cd build && \
	cmake -DBATCH_VERSION=ON -DUSE_OPENJPEG=ON .. && \
	make && make install

# Download BIDS Manager
RUN cd / && \
    git clone https://github.com/ellisdg/BIDSManager.git

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    pandas \
    pydicom

ENV PYTHONPATH /BIDSManager:$PYTHONPATH

ENTRYPOINT ["python3", "/BIDSManager/convert.py"]