import os, time
import requests
import logging

logging.basicConfig(
    filename="/app/logs/streaming_app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("streaming_apps")

image_directory = '/app/images'

YOLO_API_URL = 'http://yolov8_server:5000/stream'

def send_image_to_yolo(image_path):
    logger.info(f"Sending image: {image_path}")
    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                YOLO_API_URL,
                files={"file": img_file}
            )
            if response.status_code == 200:
                logger.info(f"Successfully processed {image_path}")
            else:
                logger.error(f"Failed to process {image_path}, Status Code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}")

def process_images():
    for filename in os.listdir(image_directory):
        if filename.endswith('jpg') or filename.endswith('png'):
            image_path = os.path.join(image_directory, filename)
            send_image_to_yolo(image_path=image_path)

if __name__ == '__main__':
    logger.info(f"{__name__} i am up...")
    while True:
        process_images()
        time.sleep(5)