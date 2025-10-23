FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 wget git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code and models
COPY app /app
COPY models /models

EXPOSE 5000

CMD ["python", "yolov8_api.py"]
