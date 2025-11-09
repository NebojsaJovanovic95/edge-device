import asyncio, tempfile, os, json, logging
from ultralytics import YOLO

from src.DbUtil import DbUtil
from src.image_storage import ImageStorage
from src.config import settings

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
db = DbUtil(settings.DB_PATH)
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

image_queue: asyncio.Queue[tuple[bytes, str]] = asyncio.Queue()

async def enqueue_image(image_bytes: bytes, filename: str):
    """Adds an image to the processing queue."""
    await image_queue.put((image_bytes, filename))   
    logging.info(f"[{NAME}] Queued image: {filename}") 

async def process_queue():
    """Continuously process images from the queue."""
    logger.info(f"[{NAME}] Starting background YOLO worker...")
    while True:
        image_bytes, filename = await image_queue.get()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_bytes)
                tmp.seek(0)
                local_path = local_storage.save_image(tmp, filename=filename)

            results = model(str(local_path))
            detection_data = results[0].to_json()

            with open(local_path, "rb") as f:
                minio_storage.save_image(f, filename)

            db.insert_detection(
                str(local_path),
                detection_data
            )
            logger.info(f"[{NAME}] Processed and uploaded {filename}")

            os.remove(local_path)
        
        except Exception as e:
            logger.info(f"[{NAME}] Error processing {filename}: {e}")
        finally:
            image_queue.task_done()