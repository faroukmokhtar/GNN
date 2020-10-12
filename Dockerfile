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

# Create the environment:
SHELL ["conda", "run", "-n", "ml-latest", "/bin/bash", "-c"]

RUN conda install -c conda-forge numpy uproot tensorflow xrootd scikit-learn matplotlib tqdm 

ENV CUDA=cu101

ENV TORCH=1.5.0

RUN pip install torch-scatter==latest+${CUDA} -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-sparse==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-cluster==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-spline-conv==latest+${CUDA}  -f https://pytorch-geometric.com/whl/torch-${TORCH}.html \
    && pip install torch-geometric

USER $NB_USER
WORKDIR /home/$NB_USER

ENV USER=${NB_USER}
