import asyncio, tempfile, os, logging, pickle, json
from ultralytics import YOLO

from src.db_util import db
from src.image_storage import local_storage, minio_storage
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

        logger.info(f"[{NAME}] Got item from Redis Queue...")
        _, serialized = data
        try:
            image_bytes, filename = pickle.loads(serialized)
            tmp_path = None

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            ) as tmp:
                tmp.write(image_bytes)
                tmp.flush()
                tmp_path = tmp.name

            results = await asyncio.to_thread(
                model,
                tmp_path
            )

            detection_data = json.loads(results[0].to_json())

            with open(tmp_path, "rb") as f:
                minio_path = minio_storage.save_image(f, filename)

            db.insert_detection(
                image_path=str(minio_path),
                detection_data=detection_data
            )
            logger.info(f"[{NAME}] Processed and uploaded {filename}")

            os.remove(tmp_path)
        
        except Exception as e:
            logger.exception(f"[{NAME}] Error processing {filename}: {e}")