FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get -y install tzdata git make openssl curl xz-utils file wget xsel vim\
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get -y install language-pack-ja \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set up Python
RUN apt-get update \
    && apt-get -y install --no-install-recommends libsqlite3-dev libbz2-dev libncurses5-dev libgdbm-dev liblzma-dev libssl-dev tcl-dev tk-dev libreadline-dev libffi-dev \
         libxcb-shm0-dev libxcb-xfixes0-dev libxcb1-dev libasound2 libSDL2-2.0 libva2 libva-drm2 libva-x11-2 libvdpau1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Update the package repository and install essential packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && apt-get clean

# Upgrade pip to the latest version
RUN python3 -m pip install --upgrade pip

# Clean up the package cache to reduce image size
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Create user
ARG USERNAME=user
ARG GROUPNAME=user
ARG UID=1011
ARG GID=1011
ARG APP_ROOT=/workspace
RUN groupadd -g $GID $GROUPNAME && \
    useradd -l -m -s /bin/bash -u $UID -g $GID $USERNAME
RUN mkdir -p $APP_ROOT && chown $USERNAME:$GROUPNAME $APP_ROOT
USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

ENV HOME /home/${USERNAME}
RUN git clone https://github.com/yyuu/pyenv.git ~/.pyenv && \
    git clone https://github.com/yyuu/pyenv-pip-rehash.git ~/.pyenv/plugins/pyenv-pip-rehash && \
    git clone https://github.com/yyuu/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/bin:$PATH
RUN echo "eval \"\$(pyenv init -)\"" >> ~/.bashrc && \
    echo "eval \"\$(pyenv virtualenv-init -)\"" >> ~/.bashrc
ENV PYTHON_VERSION 3.10.4
RUN env PYTHON_CONFIGURE_OPTS="--enable-shared" ~/.pyenv/bin/pyenv install $PYTHON_VERSION && \
    ~/.pyenv/bin/pyenv virtualenv $PYTHON_VERSION rag_app && \
    ~/.pyenv/bin/pyenv global rag_app && \
    ~/.pyenv/bin/pyenv rehash

WORKDIR $APP_ROOT
COPY --chown=$USERNAME:$GROUPNAME requirements.txt .
RUN ~/.pyenv/shims/pip install --upgrade pip && \
    ~/.pyenv/shims/pip install --upgrade setuptools && \
    ~/.pyenv/shims/pip install -r requirements.txt
COPY --chown=$USERNAME:$GROUPNAME . .
ENV PYTHONPATH $APP_ROOT:$PYTHONPATH

# Create directory
USER root
RUN mkdir -p /var/log/rag-api && chown $USERNAME:$GROUPNAME /var/log/rag-api
USER $USERNAME

WORKDIR $APP_ROOT
#ENTRYPOINT ["/tini", "--"]
CMD ["bash", "-c", "~/.pyenv/shims/python main.py"]
