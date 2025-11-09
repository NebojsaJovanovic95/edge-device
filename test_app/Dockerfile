# Base image with Python
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create a directory for outputs inside the working directory
RUN mkdir -p /app/output
RUN chmod -R 777 /app/output

# Copy your test script, requirements, and test image
COPY *.py .
COPY requirements.test.txt .
COPY test.jpg .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.test.txt

# Command to run your test script
CMD ["python", "test_post.py"]
