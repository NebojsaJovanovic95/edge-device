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
    MODEL_PATH
)

model = YOLO(MODEL_PATH)
NAME = "YOLOv8_MODEL"

async def process_model_queue():
    print(f"[{NAME}] Worker started, listening for model requests...")
    while True:
        item = await redis_client.blpop(REDIS_MODEL_REQUEST_QUEUE, timeout=5)
        if not item:
            await asyncio.sleep(0.1)
            continue

        _, serialized = item
        try:
            image_bytes, metadata = pickle.loads(serialized)
            filename = metadata.get("filename", "unknown.jpg")

            # Write image to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_bytes)
                tmp.flush()
                tmp_path = tmp.name

            # Run YOLO detection
            results = await asyncio.to_thread(model, tmp_path)
            detection_data = json.loads(results[0].tojson())

            # Send results back to results queue
            result_payload = pickle.dumps({
                "filename": filename,
                "detection": detection_data
            })
            await redis_client.rpush(REDIS_MODEL_RESULT_QUEUE, result_payload)

            print(f"[{NAME}] Processed {filename}, results pushed to results queue")
            os.remove(tmp_path)

        except Exception as e:
            print(f"[{NAME}] Error processing request: {e}")

async def main():
    await process_model_queue()

if __name__ == "__main__":
    asyncio.run(main())
