# Edge Device Object Detection

# Project structure
```
edge-device/
├── Dockerfile                  # Main YOLOv8 API server image
├── Dockerfile.test             # Test client container
├── README.md
├── app/
│   ├── src/                    # (Optional) additional source files
│   └── yolov8_api.py           # FastAPI YOLOv8 server
├── devcontainer/
│   └── devcontainer.json       # VS Code / Dev Container config
├── models/
│   └── yolov8n.pt              # Pre-downloaded YOLOv8 model
├── output/
│   ├── detections.log          # Inference logs
│   └── output_with_boxes.jpg   # Sample annotated output
├── requirements.txt            # Server dependencies
├── requirements.test.txt       # Test dependencies
└── test_app/
    ├── test.jpg                # Sample test image
    ├── test_detection_id.py
    ├── test_detections.py
    ├── test_post.py            # POST request test script
    ├── test_stream.py
    └── util.py                 # Helper functions

7 directories, 16 files
```