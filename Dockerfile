# Use PyTorch with CUDA 13.0 runtime
FROM pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime

# Set working directory
WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tzdata \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (replace with your timezone if needed)
RUN ln -fs /usr/share/zoneinfo/Europe/Belgrade /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Copy requirements if you have one
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy app to container
COPY ./app /app

# Expose any ports your API may use (if using FastAPI/Flask etc.)
EXPOSE 8000

# Default command to run your YOLOv8 API
CMD ["python", "yolov8_api.py"]

