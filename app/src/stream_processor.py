import asyncio, tempfile, os, logging, pickle
from ultralytics import YOLO

from src.db_util import db
from src.image_storage import ImageStorage
from src.config import settings

from src.redis_client import redis_client

NAME = "STREAM"

os.makedirs(settings.LOG_DIR, exist_ok=True)
log_path = os.path.join(settings.LOG_DIR, "stream.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stream_processor")

model = YOLO(settings.MODEL_PATH)

local_storage: ImageStorage = ImageStorage(
    base_dir=settings.IMAGE_DIR,
    use_minio=False
)

minio_storage: ImageStorage = ImageStorage(
    base_dir=settings.IMAGE_DIR,
    use_minio=settings.USE_MINIO,
    minio_endpoint=settings.MINIO_ENDPOINT,
    minio_access_key=settings.MINIO_ACCESS_KEY,
    minio_secret_key=settings.MINIO_SECRET_KEY,
    minio_bucket=settings.MINIO_BUCKET
)

async def enqueue_image(image_bytes: bytes, filename: str):
    """Adds an image to redis queue as aserialized tuple."""
    data = pickle.dumps((image_bytes, filename))
    await redis_client.rpush(
        settings.REDIS_QUEUE_KEY,
        data
    )
    logging.info(f"[{NAME}] Queued image: {filename}") 

async def process_queue():
    """Continuously process images from Redis queue."""
    logger.info(f"[{NAME}] Starting Redis YOLO worker...")
    while True:
        data = await redis_client.blpop(
            settings.REDIS_QUEUE_KEY,
            timeout=5
        )
        if data is None:
            await asyncio.sleep(0.1)
            continue

        _, serialized = data
        try:
            image_bytes, filename = pickle.loads(serialized)

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            ) as tmp:
                tmp.write(image_bytes)
                tmp.seek(0)
                local_path = local_storage.save_image(
                    tmp,
                    filename=filename
                )

            results = model(str(local_path))
            detection_data = results[0].to_json()

            with open(local_path, "rb") as f:
                minio_path = minio_storage.save_image(f, filename)

            db.insert_detection(
                str(minio_path),
                detection_data
            )
            logger.info(f"[{NAME}] Processed and uploaded {filename}")

            os.remove(local_path)
        
        except Exception as e:
            logger.info(f"[{NAME}] Error processing {filename}: {e}")