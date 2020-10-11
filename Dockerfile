FROM ucsdets/scipy-ml-notebook:2020.2.9

LABEL maintainer="Javier Duarte <jduarte@ucsd.edu>"

USER root
#WORKDIR /root

# Install cmake and XRootD
RUN apt-get update && \
    apt-get upgrade -qq -y && \
    apt-get install -qq -y \
    python3-pip \
    cmake && \
    apt-get -y autoclean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*
ADD install_xrootd.sh install_xrootd.sh
RUN bash install_xrootd.sh && \
    rm install_xrootd.sh
ENV PATH /opt/xrootd/bin:${PATH}
ENV LD_LIBRARY_PATH /opt/xrootd/lib

#RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
#    python2 get-pip.py

RUN python3 -m pip install coffea tables mplhep setGPU comet_ml llvmlite \
    && python3 -m pip install tqdm PyYAML uproot lz4 xxhash \
    && python3 -m pip install tables \
    && python3 -m pip install -U jupyter-book

USER $NB_USER
WORKDIR /home/$NB_USER

ENV USER=${NB_USER}
