from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

import uvicorn, asyncio, tempfile, os, json
from typing import Any

from src.config import settings
from src.db_util import db
from src.image_storage import minio_storage
from src.util import DetectionResponse
from src.stream_processor import enqueue_image, process_queue
from src.util import logger

REDIS_MODEL_REQUEST_QUEUE = os.getenv("REDIS_MODEL_REQUEST_QUEUE")
REDIS_MODEL_RESULT_QUEUE = os.getenv("REDIS_MODEL_RESULT_QUEUE")
LOG_DIR = os.getenv("LOG_DIR")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
redis_client = f"redis://{REDIS_HOST}:{REDIS_PORT}"

app = FastAPI(title="YOLOv8 Edge API")


NAME: str = "yolov8_server"

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    asyncio.create_task(process_queue())

@app.post("/stream")
async def stream_image(file: UploadFile = File(...)):
    """Receive images and enqueue them for background processing."""
    contents = await file.read()
    await enqueue_image(contents, file.filename)
    return {
        "message": f"{file.filename} queued for detection"
    }

@app.get("/health")
async def health_check():
    """Health check, returns 200 if the app is running."""
    return {"status": "healthy"}

@app.post("/detect")
async def detect(
    file: UploadFile = File(...)
) -> JSONResponse:
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".jpg"
    ) as tmp:
        tmp.write(await file.read())
        tmp.seek(0)
        image_path = minio_storage.save_image(
            tmp,
            filename = file.filename
        )
        logger.info(f"[{NAME}]: Saved image with path '{image_path}'.")
        request_id = str(uuid.uuid4())

        payload = pickle.dumps({
            "request_id": request_id,
            "filename": file.filename,
            "image_bytes": image_bytes,
            "minio_path": str(minio_path),
        })

        # Send job
        await redis_client.rpush(settings.REDIS_MODEL_REQUEST_QUEUE, payload)

        # Listen for result
        result_key = f"{settings.REDIS_MODEL_RESULT_QUEUE_PREFIX}{request_id}"
        _, result_raw = await redis_client.blpop(result_key)
        result = pickle.loads(result_raw)
        detection_data = result["detection"]

    detection_data: json = results[0].tojson()

    detection_id = db.insert_frame_with_detections(
        camera_id = 0,
        image_path = str(image_path),
        raw_detections = detection_data,
        model_name = settings.MODEL_NAME
    )

    logger.info(f"[{NAME}]: Saved detection {detection_id}.")

    return JSONResponse(
        {
            "message": "Detection complete",
            "id": detection_id,
            "image": file.filename,
            "path": str(image_path),
            "detection": json.loads(detection_data)
        }
    )

@app.get("/detections")
async def get_all_detections(
    frame_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    confidence: Optional[float] = Query(None, ge = 0.0, le = 1.0),
    limit: int = Query(20, ge = 1, le = 100),
    offset: int = Query(0, ge = 0)
) -> JSONResponse:
    detections = db.get_detections(
        frame_id=frame_id,
        class_name=class_name,
        confidence=confidence,
        limit=limit,
        offset=offset
    )
    return JSONResponse(
        {
            "count": len(detections),
            "detections": detections
        }
    )

@app.get("/frames")
async def get_all_frames(
    camera_id: Optional[int] = Query(None),
    model_name: Optional[str] = Query(None),
    after_ts: Optional[int] = Query(None),
    limit: int = Query(20, ge = 1, le=100),
    offset: int = Query(0, ge = 0)
) -> JSONResponse:
    frames = db.get_frames(
        camera_id=camera_id,
        model_name=model_name,
        created_after=after_ts,
        limit=limit,
        offset=offset
    )
    return JSONResponse(
        {
            "count": len(frames),
            "frames": frames
        }
    )

@app.get("/detection/{id}")
async def get_detection(id: int):
    detection = db.get_detection(id)
    if detection is None:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )
    logger.info(f"[{NAME}]: Fetched detection: s{detection}")
    
    frame = db.get_frame_by_id(frame_id=detection["frame_id"])
    image_path: str = frame["image_path"]

    def image_stream() -> Any:
        with minio_storage.load_image(image_path) as image_file:
            while chunk := image_file.read(1024):
                yield chunk
    
    return StreamingResponse(
        image_stream(),
        media_type="image/jpeg",
        headers={
            "X-Detection-Data": json.dumps(detection)
        }
    )

@app.get("/frame/{id}")
async def get_frame(id: int):
    frame_with_detections = db.get_frame_by_id(id)
    if frame_with_detections["frame"] is None:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )
    logger.info(f"[{NAME}]: Fetched detection: s{frame_with_detections}")
    
    image_path: str = frame_with_detections["frame"]["image_path"]
    detection_data: list[dict[str, Any]] = frame_with_detections["detections"]

    def image_stream() -> Any:
        with minio_storage.load_image(image_path) as image_file:
            while chunk := image_file.read(1024):
                yield chunk
    
    return StreamingResponse(
        image_stream(),
        media_type="image/jpeg",
        headers={
            "X-Detection-Data": json.dumps(detection_data)
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
