FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-devel

ENV TZ=Etc/UTC \
  DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git build-essential libgoogle-perftools-dev ffmpeg
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/nightly/cu121
ENV TORCH_CUDA_ARCH_LIST=All
ENV MAX_JOBS=4
ENV LD_PRELOAD=libtcmalloc.so
RUN pip install git+https://github.com/Dao-AILab/flash-attention.git@v2.3.6 --no-build-isolation

COPY app/ .

CMD ["python", "api.py"]