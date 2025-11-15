# Build
## yolov8_server
podman build -t yolov8_server -f Dockerfile app/.
## yolov8_client
podman build -t yolov8_client -f Dockerfile test_app/.
## image_stream
podman build -t image_stream -f Dockerfile streaming_app/.
# Run
## podman network
podman network create yolov8_net
## minio
podman run -d --replace \
    --name minio \
    --network yolov8_net \
    --env-file $(pwd)/minio/minio.env \
    -p 9000:9000 \
    -p 9001:9001 \
    -v $(pwd)/data:/data:Z \
    minio
## postgres
podman run --replace -d \
  --name postgres \
  --network yolov8_net \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=supersecret \
  -e POSTGRES_DB=mydb \
  -v ./postgres_data:/var/lib/postgresql:Z \
  -p 5432:5432 \
  docker.io/postgres:latest
## redis
podman run --replace -d \
  --name redis \
  --network yolov8_net \
  -p 6379:6379 \
  docker.io/redis:7
## yolov8_server
podman run -d --replace\
  --name yolov8_server \
  --network yolov8_net \
  -e MPLCONFIGDIR=/tmp/matplotlib \
  -e YOLO_CONFIG_DIR=/tmp/ultralytics \
  -v ./logs:/app/logs:Z \
  -v ./models:/app/models:Z \
  -p 5000:5000 \
  yolov8_server:latest
## yolov8_client
podman run -d --replace\
  --name test_app \
  --network yolov8_net \
  --env-file .env \
  --env-file .env.private \
  -v ./logs:/app/logs:Z \
  test_app:latest
## image_stream
podman run -d --replace\
  --name streaming_app \
  --network yolov8_net \
  --env-file .env \
  --env-file .env.private \
  -v ./logs/streaming_app:/app/logs:Z \
  -v ./images:/app/images:Z \
  streaming_app:latest
# logs
podman logs yolov8_server
podman logs yolov8_client