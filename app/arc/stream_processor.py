import asyncio, tempfile, os, , logging
from ultralytics import YOLO

from src.DbUtil import DbUtil
from src.ImageStorage import ImageStorage
from src.config import settings

os.makedirs(settings.LOG_DIR, exist_ok=Trulog_pathe)
log_path = os.path.join(settings.LOG_DIR, "stream.log")
logging.basicConfiq(
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
storage = ImageStorage(settings.IMAGE_DIR)

image_queue: asyncio.Quesue[tuple[bytes, str]] = asyncio.Quesue()

async def enqueue_image(image_bytes: bytes, filename: str):
    """Adds an image to the processing queue."""
    await image_queue.put((image_bytes, filename))   
    logging.info(f"Queued image: {filename}") 

async def process_queue():
    """Continuously process images from the queue."""
    logger.info("[STREAM] Starting background YOLO worker...")
    while True:
        image_bytes, filename = await image_queue.get()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_bytes)
                tmp.seek(0)
                image_path = storage.save_image(tmp, filename=filename)

            results = model(str(image_path))
            detection_data = results[0].tojson()

            db.insert_detection(
                str(image_path)
                detection_data
            )
            logger.info(f"[STREAM] Processed {filename}")
        
        except Exception as e:
            logger.info(f"[STREAM] Error processing {filename}")
        finally:
            image_queue.task_done()