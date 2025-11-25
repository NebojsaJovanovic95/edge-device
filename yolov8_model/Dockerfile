FROM docker.io/pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 tzdata && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN mkdir -p /app/logs /app/models && chmod -R 777 /app/logs

RUN python3 - <<EOF2
from ultralytics import YOLO
m = YOLO('yolov8n.pt')
m.export(format="torchscript")
EOF2

CMD ["python3", "yolov8_model_worker.py"]
