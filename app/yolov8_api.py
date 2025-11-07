from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO

import uvicorn, asyncio, tempfile, os, json
from typing import Any

from src.config import settings
from src.DbUtil import DbUtil
from src.ImageStorage import ImageStorage
from src.Util import DetectionResponse
from src.stream_processor import enqueue_image, process_queue

app = FastAPI(title="YOLOv8 Edge API")

model: YOLO = YOLO("/models/yolov8n.pt")

# Initialize singletons using config paths
model: YOLO = YOLO(settings.MODEL_PATH)
db: DbUtil = DbUtil(settings.DB_PATH)
storage: ImageStorage = ImageStorage(settings.IMAGE_DIR)

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
        detection_data
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
        {"detections": db.get_all_detections()}
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