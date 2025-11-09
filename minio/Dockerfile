# Use official MinIO image as base
FROM docker.io/minio/minio:latest

# Set environment variables for access key and secret
ENV MINIO_ROOT_USER=minio_access_key
ENV MINIO_ROOT_PASSWORD=minio_secret_key

# Expose MinIO API port
EXPOSE 9000 9001

# Default command to start MinIO server storing data in /data
CMD ["server", "/data", "--console-address", ":9001"]
