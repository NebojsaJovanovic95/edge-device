# Use Python as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the streaming app code into the container
COPY . /app

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod -R 777 /app
RUN mkdir -p /app/logs

# Run the image processor script by default
CMD ["python", "image_processor.py"]
