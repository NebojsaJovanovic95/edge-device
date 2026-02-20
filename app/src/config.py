import os
from functools import cached_property
from pathlib import Path
import redis.asyncio as aioredis


MODEL_NAME: str = "YOLOv8"
BASE_DIR: str = "/app"

CACHE_DB_PATH: str = os.path.join(BASE_DIR, "cache", "detection.db")
IMAGE_DIR: str = os.path.join(BASE_DIR, "images")
LOG_DIR: str = os.getenv("LOG_DIR")

MAX_SERVERS: int = 20

USE_MINIO: bool = True
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET: str = os.getenv("MINIO_BUCKET")

POSTGRES_TABLE_NAME: str = os.getenv("POSTGRES_TABLE_NAME")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
POSTGRES_PORT: int = os.getenv("POSTGRES_PORT")
POSTGRES_DB: str = os.getenv("POSTGRES_DB")
POSTGRES_USER: str = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DSN: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

REDIS_HOST: str = os.getenv("REDIS_HOST")
REDIS_PORT: int = os.getenv("REDIS_PORT")
REDIS_DB: int = os.getenv("REDIS_DB")

REDIS_TASK_QUEUE: str = os.getenv("REDIS_TASK_QUEUE")
REDIS_MODEL_REQUEST_QUEUE: str = os.getenv("REDIS_MODEL_REQUEST_QUEUE")
REDIS_MODEL_RESULT_QUEUE: str = os.getenv("REDIS_MODEL_RESULT_QUEUE")
REDIS_STORAGE_QUEUE: str = os.getenv("REDIS_STORAGE_QUEUE")

redis_client: aioredis.Redis = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=False  # store raw bytes
)
