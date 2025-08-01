FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG CONFIG_FILE=config/chat_with_minicpm.yaml

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# 替换为清华大学的APT源
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 更新包列表并安装必要的依赖
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get install -y python3.10 python3.10-dev python3-pip git

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

ARG WORK_DIR=/root/open-avatar-chat
WORKDIR $WORK_DIR

#安装核心依赖
COPY /mnt/data/OpenAvatarChat/install.py $WORK_DIR/install.py
COPY /mnt/data/OpenAvatarChat/pyproject.toml $WORK_DIR/pyproject.toml
COPY /mnt/data/OpenAvatarChat/src/third_party $WORK_DIR/src/third_party
RUN pip install uv && \
    uv venv --python 3.10 && \
    uv sync --no-install-workspace

ADD /mnt/data/OpenAvatarChat/src $WORK_DIR/src

#安装config依赖
RUN echo "Using config file: ${CONFIG_FILE}"
COPY $CONFIG_FILE /tmp/build_config.yaml
RUN uv run install.py \
    --config /tmp/build_config.yaml \
    --uv \
    --skip-core && \
    rm /tmp/build_config.yaml

ADD /mnt/data/OpenAvatarChat/resource $WORK_DIR/resource
ADD /mnt/data/OpenAvatarChat/scripts $WORK_DIR/scripts
ADD /mnt/data/OpenAvatarChat/.env* $WORK_DIR/

WORKDIR $WORK_DIR
ENTRYPOINT ["uv", "run", "src/demo.py"]
