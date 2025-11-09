from pydantic import BaseModel
import logging


class DetectionResponse(BaseModel):
    id: str
    result: dict

logging.basicConfig(
    filename="/app/logs/yolov8_server.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("yolov8_server")