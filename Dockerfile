FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive
ENV MAMBA_ROOT_PREFIX=/opt/mamba
ENV PATH="${MAMBA_ROOT_PREFIX}/bin:${MAMBA_ROOT_PREFIX}/condabin:/usr/local/bin:${PATH}"

# Install system utilities and micromamba bootstrap dependencies.
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y ca-certificates curl bzip2 pigz && \
    apt-get clean -y && apt-get autoclean -y && apt-get autoremove -y

# Install micromamba and use conda-forge packages for runtime dependencies.
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | \
    tar -xj -C /usr/local/bin --strip-components=1 bin/micromamba && \
    micromamba install -y -n base -c conda-forge python pip dcm2niix pandas pydicom && \
    micromamba clean --all --yes

# Install BIDS Manager from the local build context.
WORKDIR /BIDSManager
COPY . /BIDSManager
RUN pip install --no-cache-dir .

# Smoke-test key tools and imports at build time.
RUN python --version && \
    python -c "import shutil, subprocess; assert shutil.which('dcm2niix'), 'dcm2niix not found in PATH'; subprocess.run(['dcm2niix', '--version'], check=False); import bidsmanager, pandas, pydicom; print('installation_ok')"

ENTRYPOINT ["python", "/BIDSManager/convert.py"]
