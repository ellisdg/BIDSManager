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
    apt-get install -y python3 python3-pip python3-venv && \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Activate the virtual environment and install packages
RUN /opt/venv/bin/pip install --no-cache-dir \
    pandas \
    pydicom

# Set the virtual environment as the default Python environment
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONPATH /BIDSManager:$PYTHONPATH

ENTRYPOINT ["python3", "/BIDSManager/convert.py"]