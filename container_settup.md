# Build
## yolov8_server
podman build -t yolov8_server -f Dockerfile .
## yolov8_client
podman build -t yolov8_client -f Dockerfile.test .
# Run
## yolov8_server
podman run -d --rm --replace --name yolov8_server --network yolov8_net -p 5000:5000 yolov8_server
## yolov8_client
podman run -d --replace --name yolov8_client --network yolov8_net -v $(pwd)/output:/app/output yolov8_client
# logs
podman logs yolov8_server
podman logs yolov8_client