import os
from pydantic_settings import BaseSettings
from functools import cached_property
from pathlib import Path

class Settings(BaseSettings):
    BASE_DIR: str = "/app"

    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "yolov8n.pt")
    CACHE_DB_PATH: str = os.path.join(BASE_DIR, "cache", "detection.db")
    IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    YOLO_CONFIDENCE_THRESHOLD: float = 0.25

    USE_MINIO: bool = True
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ROOT_USER: str = "minio_access_key"
    MINIO_ROOT_PASSWORD: str = "minio_secret_key"
    MINIO_BUCKET: str = "processed-images"

    POSTGRES_TABLE_NAME: str = "detections"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_DB: str = "mydb"
    POSTGRES_USER: str = "myuser"
    POSTGRES_PASSWORD: str = "supersecret"
    POSTGRES_DSN: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_QUEUE_KEY: str

    # class Config:
    #     env_file = [".env", ".env.private"]
    #     env_file_encoding = "utf-8"

settings = Settings()
