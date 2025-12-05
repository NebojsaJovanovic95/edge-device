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

YOLO_API_URL: str = 'http://yolov8_server:5000/stream'
RTSP_CAMERA_SOURCE: str = os.getenv(
    "RTSP_CAMERA_SOURCE"
)
CAMERA_SOURCE: str = os.getenv(
    "CAMERA_SOURCE"
)
FALLBACK_CAMERA_SOURCE: str = os.getenv(
    "FALLBACK_CAMERA_SOURCE"
)
FRAME_INTERVAL: int = int(os.getenv("FRAME_INTERVAL", 5))
HASH_DIFF_THRESHOLD = 1000
SEND_INTERVAL = 1.0

def frame_hash(frame: np.ndarray) -> int:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (64,64))
    return int(hashlib.md5(resized).hexdigest(), 16)

def get_camera_source():
    """
    Return the first available source:
    1. RTSP /env RTSP_CAMERA_SOURCE
    2. Local webcam /dev/video (linux)
    3. Fallback video (inferior windows device)
    Returns cv2.VideoCapture object and a string indicating source
    """
    sources = []

    if RTSP_CAMERA_SOURCE:
        sources.append((RTSP_CAMERA_SOURCE, "camera"))

    if os.name =="posix" and os.path.exists(CAMERA_SOURCE):
        sources.append((CAMERA_SOURCE, "webcam"))

    sources.append((FALLBACK_CAMERA_SOURCE, "file"))

    for src, label in sources:
        cap = cv2.VideoCapture(src)
        if cap.isOpened():
            logger.info(f"Using {label} source: {src}")
            return cap, label
        else:
            logger.warning(f"Failed to open {label} source: {src}")

    logger.error("No camera/video available, using synthetic frames")
    return None, "synthetic"

def synthetic_frame():
    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8
    )
    cv2.putText(
        frame,
        text,
        (20, 40),
        cv2.FRONT_HERSHEY_SYMPLEX,
        1,
        (255, 255, 255),
        2
    )
    timestamp = datetime.now(),strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        frame,
        timestamp,
        (20, 80),
        cv2.FRONT_HERSHEY_SYMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    return frame

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
    prev_time = time.time()

    cap, mode = get_camera_source()

    while True:
        ret, frame = cap.read()

        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                logger.info(f"[{__name__}]: Failed to read frame.")
                await asyncio.sleep(2)
                cap, mode = get_camera_source()
                continue
        else:
            frame = synthetic_frame()

        current_time = time.time()
        if current_time - prev_time < SEND_INTERVAL:
            await asyncio.sleep(0.01)
            continue

        prev_time = current_time
        
        try:
            current_hash = frame_hash(frame)
        except Exception:
            current_hash = None

        if (prev_hash is None
            or abs(current_hash - prev_hash) > HASH_DIFF_THRESHOLD):
            prev_hash = current_hash
            _, buf = cv2.imencode('.jpg', frame)
            await send_image_to_yolo(
                session,
                image_bytes=buf.tobytes()
            )
        await asyncio.sleep(0.01)

async def main():
    logger.info(f"{__name__} i am up...")
    async with aiohttp.ClientSession() as session:
        while True:
            await process_video(session)
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
