import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BASE_DIR: str = "/app"

    MODEL_PATH: str = os.path.join(BASE_DIR, "models", "yolov8n.pt")
    DB_PATH: str = os.path.join(BASE_DIR, "detection.db")
    IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")

    YOLO_CONFIDENCE_THRESHOLD: float = 0.25

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()