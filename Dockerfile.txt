FROM gitlab-registry.nautilus.optiputer.net/prp/jupyterlab:latest

LABEL maintainer="Javier Duarte <jduarte@ucsd.edu>"

USER root
WORKDIR /root

# Install cmake and XRootD
RUN apt-get update && \
    apt-get upgrade -qq -y && \
    apt-get install -qq -y \
    python-pip \
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

USER $NB_USER
WORKDIR /home/$NB_USER

ENV USER=${NB_USER}

RUN set -x \
    && pip install coffea tables mplhep setGPU comet_ml llvmlite --ignore-installed \
    && pip install tqdm PyYAML uproot lz4 xxhash \
    && pip install tables \
    && pip install onnxruntime-gpu \
    && pip install -U jupyter-book

RUN set -x \ 
    && conda install -c conda-forge xrootd -y

ENV CUDA=cu102

ENV TORCH=1.5.0

ENV TORCH_CUDA_ARCH_LIST=6.0,7.0
    
RUN set -x \
    && pip install torch-scatter==latest+${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-sparse==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-cluster==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-spline-conv==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-geometric \ 
    && pip install dgl-$CUDA \
    && pip install tfdlpack-gpu

RUN set -x \
    && fix-permissions /home/$NB_USER
