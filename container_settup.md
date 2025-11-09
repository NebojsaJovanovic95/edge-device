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
## yolov8_server
podman run -d --rm --replace --name yolov8_server --network yolov8_net -p 5000:5000 yolov8_server
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