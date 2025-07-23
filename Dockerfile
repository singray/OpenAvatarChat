FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG CONFIG_FILE=config/glut_tts.yaml

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# 替换为清华大学的APT源
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 更新包列表并安装必要的依赖
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get install -y python3.10 python3.10-dev python3-pip python3.10-venv git

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

ARG WORK_DIR=/root/open-avatar-chat
WORKDIR $WORK_DIR

# 创建Python虚拟环境并设置路径
ENV VENV_PATH=$WORK_DIR/venv
RUN python3 -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# 配置pip源
RUN mkdir -p ~/.pip && \
    echo "[global]" > ~/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> ~/.pip/pip.conf && \
    echo "trusted-host = mirrors.aliyun.com" >> ~/.pip/pip.conf

# 安装核心依赖
COPY ./install.py $WORK_DIR/install.py
COPY ./pyproject.toml $WORK_DIR/pyproject.toml
COPY ./src/third_party $WORK_DIR/src/third_party

# 使用pip直接安装依赖，替代uv
RUN pip install --timeout 300 --retries 5 --no-cache-dir --upgrade pip && \
    pip install --timeout 300 --retries 5 --no-cache-dir .

ADD ./src $WORK_DIR/src

# 安装config依赖
RUN echo "Using config file: config/glut_tts.yaml"
COPY config/glut_tts.yaml /tmp/build_config.yaml
RUN python install.py \
    --config /tmp/build_config.yaml \
    --skip-core && \
    rm /tmp/build_config.yaml

ADD ./resource $WORK_DIR/resource
ADD ./scripts $WORK_DIR/scripts

WORKDIR $WORK_DIR
# 使用Python直接运行应用
#ENTRYPOINT ["python", "src/demo.py"]