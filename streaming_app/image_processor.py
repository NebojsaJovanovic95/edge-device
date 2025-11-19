import os, time, cv2
import logging
import aiohttp
import asyncio
import numpy as np
from io import BytesIO
import hashlib

logging.basicConfig(
    filename="/app/logs/streaming_app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("streaming_apps")

image_directory = '/app/images'

YOLO_API_URL = 'http://yolov8_server:5000/stream'
VIDEO_PATH = "/app/input_video.mp4"
FRAME_INTERVAL = 5
HASH_DIFF_THRESHOLD = 1000

def frame_hash(frame: np.ndarray) -> int:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (64,64))
    return int(hashlib.md5(resized).hexdigest(), 16)

async def send_image_to_yolo(
    session,
    image_path=None,
    image_bytes=None
):
    logger.info(f"Sending image: {image_path}")
    try:
        if image_path:
            logger.info(f"Sending image file: {image_path}")
            with open(image_path, 'rb') as img_file:
                data = {'file': img_file}
                async with session.post(
                    YOLO_API_URL,
                    data=data
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully processed {image_path}")
                    else:
                        logger.error(f"Failed to process {image_path}, Status Code: {response.status}")
        elif image_bytes:
            logger.info(f"Sending image from bytes")
            if not isinstance(image_bytes, BytesIO):
                image_bytes = BytesIO(image_bytes)
            data = {'file': image_bytes}
            async with session.post(
                YOLO_API_URL,
                data=data
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully sent image bytes")
                else:
                    logger.error(f"Failed to send image bytes, Status: {response.status}")
        else:
            logger.error("No image provided to send")
    except Exception as e:
        logger.error(f"Error sending image: {str(e)}")

async def process_images(image_bytes: bytes):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for filename in os.listdir(image_directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(image_directory, filename)
                tasks.append(
                    send_image_to_yolo(
                        session=session,
                        image_path=image_path
                    )
                )
        await asyncio.gather(*tasks)


async def process_video(session):
    prev_hash = None
    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.info(f"[{__name__}]: End of video or failed to read fram.")
            break
        
        frame_count += 1
        if frame_count % FRAME_INTERVAL != 0:
            continue
        
        current_hash = frame_hash(frame)
        if (prev_hash is None
            or abs(current_hash - prev_hash) > HASH_DIFF_THRESHOLD):
            prev_hash = current_hash
            _, buf = cv2.imencode('.jpg', frame)
            frame_bytes = buf.tobytes()
            await send_image_to_yolo(
                session,
                image_bytes=frame_bytes
            )

async def main():
    logger.info(f"{__name__} i am up...")
    async with aiohttp.ClientSession() as session:
        while True:
            await process_video(session)
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
