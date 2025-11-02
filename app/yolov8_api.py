from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from ultralytics import YOLO
import uvicorn
import tempfile, os, json
from typing import Any

from src.DbUtil import DbUtil
from src.ImageStorage import ImageStorage

app = FastAPI(title="YOLOv8 Edge API")

model: YOLO = YOLO("/models/yolov8n.pt")

DB_PATH = "/app/detections.db"
db: DbUtil = DbUtil(DB_PATH)

IMAGE_BUCKET_BASE_DIR = "/app/images"
storage: ImageStorage = ImageStorage(IMAGE_BUCKET_BASE_DIR)

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
            "detection": results[0].tojson()
        }
    )

@app.get("/detections")
async def get_all_detections() -> JSONResponse:
    return JSONResponse(
        {"detections": db.get_all_detections()}
    )

@app.get("/detection/{id}")
async def get_detection(id: int) -> StreamingResponse | JSONResponse:
    detection = db.get_detection_by_id(id)
    if detection is None:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )
    
    image_path: str = detection["image_path"]
    detection_data: list[dict[std, Any]] = json.loads(detection["detection_data"])

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
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5000)