from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO

import uvicorn, asyncio, tempfile, os, json
from typing import Any

from src.config import settings
from src.db_util import DetectionDb
from src.image_storage import ImageStorage
from src.util import DetectionResponse
from src.stream_processor import enqueue_image, process_queue

from src.redis_client import redis_client

app = FastAPI(title="YOLOv8 Edge API")

# Initialize singletons using config paths
model: YOLO = YOLO(settings.MODEL_PATH)
db: DetectionDb = DetectionDb(
    postgres_dsn=settings.POSTGRES_DSN,
    sqlite_path=settings.CACHE_DB_PATH
)
storage: ImageStorage = ImageStorage(
    base_dir=settings.IMAGE_DIR,
    use_minio=settings.USE_MINIO,
    minio_endpoint=settings.MINIO_ENDPOINT,
    minio_access_key=settings.MINIO_ACCESS_KEY,
    minio_secret_key=settings.MINIO_SECRET_KEY,
    minio_bucket=settings.MINIO_BUCKET
)

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
        image_path = storage.save_image(
            tmp,
            filename = file.filename
        )
    
    results = model(str(image_path))
    detection_data: json = results[0].tojson()

    detection_id = db.insert_detection(
        str(image_path),
        json.loads(detection_data)
    )

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
async def get_all_detections() -> JSONResponse:
    return JSONResponse(
        {"detections": db.get_recent(limit=20)}
    )

@app.get("/detection/{id}")
async def get_detection(id: int):
    detection = db.get_detection_by_id(id)
    if detection is None:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )
    print(f"Fetched detection: s{detection}")
    
    image_path: str = detection["image_path"]
    detection_data: list[dict[str, Any]] = json.loads(detection["detection_data"])

    def image_stream() -> Any:
        with storage.load_image(image_path) as image_file:
            while chunk := image_file.read(1024):
                yield chunk
    
    return StreamingResponse(
        image_stream(),
        media_type="image/jpeg",
        headers={
            "X-Detection-Data": json.dumps(detection_data)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)