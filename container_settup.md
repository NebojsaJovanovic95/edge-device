# Build
## minio
podman build -t minio -f Dockerfile minio/.
## postgres
podman build -t custom_postgres .
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
# postgres
podman run -d --replace \
    --name postgres \
    --network yolov8_net \
    --env-file $(pwd)/postgres.env \
    -v $(pwd)/postgres_data:/var/lib/postgresql/data:Z \
    -p 5432:5432 \
    custom_postgres
## yolov8_server
podman run -d --replace --name yolov8_server \
    --network yolov8_net \
    -v $(pwd)/logs:/app/logs \
    -p 5000:5000 \
    yolov8_server
## yolov8_client
podman run -d --replace --name yolov8_client \
    --network yolov8_net \
    -v $(pwd)/output:/app/output \
    yolov8_client
## image_stream
podman run -d --replace --name image_stream \
    --network yolov8_net \
    -v $(pwd)/images:/app/images \
    -v $(pwd)/logs:/app/logs \
    image_stream
# logs
podman logs yolov8_server
podman logs yolov8_client