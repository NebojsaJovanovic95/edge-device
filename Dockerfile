# Use PyTorch with CUDA 13.0 runtime
FROM docker.io/pytorch/pytorch:2.9.0-cuda13.0-cudnn9-runtime

# Set working directory
WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Install system dependencies (OpenCV runtime deps + git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    git \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone (adjust if needed)
RUN ln -fs /usr/share/zoneinfo/Europe/Belgrade /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY ./app /app

# Expose the FastAPI port
EXPOSE 5000

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "yolov8_api:app", "--host", "0.0.0.0", "--port", "5000"]
