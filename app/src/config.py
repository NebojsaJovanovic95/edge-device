import os
from functools import cached_property
from pathlib import Path
from shared_config import settings as shared_settings


class Settings:
    BASE_DIR: str = "/app"

    CACHE_DB_PATH: str = os.path.join(BASE_DIR, "cache", "detection.db")
    IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
    LOG_DIR: str = shared_settings.LOG_DIR

    YOLO_CONFIDENCE_THRESHOLD: float = 0.25

    USE_MINIO: bool = True
    MINIO_ENDPOINT: str = shared_settings.MINIO_ENDPOINT
    MINIO_ROOT_USER: str = shared_settings.MINIO_ROOT_USER
    MINIO_ROOT_PASSWORD: str = shared_settings.MINIO_ROOT_PASSWORD
    MINIO_BUCKET: str = shared_settings.MINIO_BUCKET

    POSTGRES_TABLE_NAME: str = shared_settings.POSTGRES_TABLE_NAME
    POSTGRES_HOST: str = shared_settings.POSTGRES_HOST
    POSTGRES_PORT: int = shared_settings.POSTGRES_PORT
    POSTGRES_DB: str = shared_settings.POSTGRES_DB
    POSTGRES_USER: str = shared_settings.POSTGRES_USER
    POSTGRES_PASSWORD: str = shared_settings.POSTGRES_PASSWORD
    POSTGRES_DSN: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    REDIS_HOST: str = shared_settings.REDIS_HOST
    REDIS_PORT: int = shared_settings.REDIS_PORT
    REDIS_DB: int = shared_settings.REDIS_DB
    
    REDIS_TASK_QUEUE: str = shared_settings.REDIS_TASK_QUEUE
    REDIS_MODEL_REQUEST_QUEUE: str = shared_settings.REDIS_MODEL_REQUEST_QUEUE
    REDIS_MODEL_RESULT_QUEUE: str = shared_settings.REDIS_MODEL_RESULT_QUEUE
    REDIS_STORAGE_QUEUE: str = shared_settings.REDIS_STORAGE_QUEUE

    # class Config:
    #     env_file = [".env", ".env.private"]
    #     env_file_encoding = "utf-8"

settings = Settings()
