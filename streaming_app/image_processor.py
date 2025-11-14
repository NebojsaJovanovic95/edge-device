import os, time
import logging
import aiohttp
import asyncio

logging.basicConfig(
    filename="/app/logs/streaming_app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("streaming_apps")

image_directory = '/app/images'

YOLO_API_URL = 'http://yolov8_server:5000/stream'

async def send_image_to_yolo(session, image_path):
    logger.info(f"Sending image: {image_path}")
    try:
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
    except Exception as e:
        logger.error(f"Error processing {image_path}: {str(e)}")

async def process_images():
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

async def main():
    logger.info(f"{__name__} i am up...")
    while True:
        await process_images()
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())