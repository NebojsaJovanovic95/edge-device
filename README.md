# Edge Device Object Detection

# Project Architecture

```mermaid

flowchart TB
    subgraph Streaming_App
        Stream[streaming_app]
    end

    subgraph RedisQueue
        Redis[redis]
    end

    subgraph YOLOv8_Server
        direction TB
        FAST_API[Routing requests]

        %% DetectionDB bellow FAST_API
        direction TB
        subgraph DetectionDB
            CACHE[sqllite for caching]
            PG_CLIENT[postgres connection]
        end

        %% DetectionDB bellow FAST_API
        direction TB
        subgraph YOLO_MODEL
            GPU[yolo model runs on gpu with cuda]
        end

        FAST_API <--> DetectionDB
        FAST_API <--> YOLO_MODEL
    end

    subgraph Postgres
        PG[postgres]
    end

    subgraph MinIO [Minio Object Storage]
        M[minio]
    end

    Stream --> Redis
    Redis --> FAST_API
    DetectionDB <--> PG
    DetectionDB <--> M

```

# Project structure
```
.
├── README.md
├── app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src
│   │   ├── config.py
│   │   ├── db_util.py
│   │   ├── image_storage.py
│   │   ├── postgres_util.py
│   │   ├── redis_client.py
│   │   ├── stream_processor.py
│   │   └── util.py
│   └── yolov8_api.py
├── container_settup.md
├── data
├── devcontainer
│   └── devcontainer.json
├── images
│   └── free-photo-of-downtown-toronto-street-scene-with-traffic.jpeg
├── logs
│   ├── image_processor.log
│   ├── stream.log
│   ├── stream_processor
│   └── yolov8_server.log
├── models
│   └── yolov8n.pt
├── output
│   ├── detections.log
│   └── output_with_boxes.jpg
├── podman-compose.yml
├── postgres_data  [error opening dir]
├── streaming_app
│   ├── Dockerfile
│   ├── image_processor.py
│   └── requirements.txt
└── test_app
    ├── Dockerfile
    ├── logs
    ├── requirements.test.txt
    ├── test.jpg
    ├── test_detection.py
    ├── test_detection_id.py
    ├── test_detections.py
    ├── test_post.py
    ├── test_stream.py
    └── util.py

13 directories, 34 files
```