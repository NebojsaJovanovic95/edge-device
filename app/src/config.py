import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_DIR: str = "/app"

    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "yolov8n.pt")
    CACHE_DB_PATH: str = os.path.join(BASE_DIR, "detection.db")
    IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    YOLO_CONFIDENCE_THRESHOLD: float = 0.25

    USE_MINIO: bool = True
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minio_access_key"
    MINIO_SECRET_KEY: str = "minio_secret_key"
    MINIO_BUCKET: str = "processed-images"

    POSTGRES_TABLE_NAME: str = "detections"
    POSTGRES_DSN: str = ""

    REDIS_HOST: str = "redis"
    REDIS_PORT: str = 6379
    REDIS_DB: str = 0

    REDIS_QUEUE_KEY: str = "image_queue"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()