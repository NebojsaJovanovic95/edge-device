FROM python:3.11-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install OS deps only for FastAPI, PostgreSQL, MinIO clients
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN mkdir -p /app/logs && chmod -R 777 /app/logs

EXPOSE 5000

CMD ["uvicorn", "yolov8_api:app", "--host", "0.0.0.0", "--port", "5000"]
