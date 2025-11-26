import asyncio
import pickle
import tempfile
import os
import json
from ultralytics import YOLO
from shared_config.redis_client import redis_client
from shared_config.settings import (
    REDIS_MODEL_REQUEST_QUEUE,
    REDIS_MODEL_RESULT_QUEUE,
    LOG_DIR
)
import sys
import logging
os.makedirs(LOG_DIR, exist_ok=True)
log_path = os.path.join(LOG_DIR, "yolov8_model.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("yolov8_model")

MODEL_PATH = "/app/model/yolov8n.pt"
model = YOLO(MODEL_PATH)
NAME = "YOLOv8_MODEL"

async def process_model_queue():
    logger.info(f"[{NAME}] Worker started, listening for model requests...")
    while True:
        item = await redis_client.blpop(
            REDIS_MODEL_REQUEST_QUEUE,
            timeout=5
        )
        if not item:
            await asyncio.sleep(0.1)
            continue

        _, serialized = item
        try:
            payload = pickle.loads(serialized)
            image_bytes = payload["image_bytes"]
            filename = payload.get("filename", "unknown.jpg")
            request_id = payload["request_id"]

            # Write image to temp file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            ) as tmp:
                tmp.write(image_bytes)
                tmp.flush()
                tmp_path = tmp.name

            # Run YOLO detection
            results = await asyncio.to_thread(model, tmp_path)
            detection_data = json.loads(results[0].tojson())

            # Send results back to results queue
            result_key = f"{REDIS_MODEL_RESULT_QUEUE}:{request_id}"
            result_payload = pickle.dumps({
                "filename": filename,
                "detection": detection_data
            })
            await redis_client.rpush(
                result_key,
                result_payload
            )

            logger.info(
                f"[{NAME}] Processed {filename}, results pushed to {result_key}"
            )
            os.remove(tmp_path)

        except Exception as e:
            logger.error(f"[{NAME}] Error processing request: {e}")

async def main():
    await process_model_queue()

if __name__ == "__main__":
    asyncio.run(main())
