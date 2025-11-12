import os
from pydantic_settings import BaseSettings
from functools import cached_property

class Settings(BaseSettings):
    BASE_DIR: str = "/app"

    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "yolov8n.pt")
    CACHE_DB_PATH: str = os.path.join(BASE_DIR, "detection.db")
    IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    YOLO_CONFIDENCE_THRESHOLD: float = 0.25

    USE_MINIO: bool = True
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET: str

    POSTGRES_TABLE_NAME: str = "detections"
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    @cached_property
    def POSTGRES_DSN(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_QUEUE_KEY: str

    class Config:
        env_file = [".env", ".env.private"]
        env_file_encoding = "utf-8"

settings = Settings()
