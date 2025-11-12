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
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str

    POSTGRES_TABLE_NAME: str = "detections"
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DSN: str = ""

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_QUEUE_KEY: str

    class Config:
        env_file = [".env", ".env.private"]
        env_file_encoding = "utf-8"

settings = Settings()
