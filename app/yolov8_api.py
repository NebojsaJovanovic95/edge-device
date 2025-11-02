import json
from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import tempfile, os
import sqlite3
from pathlib import Path

app = FastAPI(title="YOLOv8 Edge API")

model = YOLO("/models/yolov8n.pt")

db_path = "/app/detections.db"

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            detection_data TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    results = model(tmp_path)

    detection_data = results[0].boxes.tojson()


    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO detections (image_path, detection_data) VALUES (?, ?)",
        (tmp_path, detection_data)
    )
    conn.commit()
    conn.close()
    os.remove(tmp_path)

    return JSONResponse({
        "message": "Detection complete and stored!"
    })

@app.get("/detections")
async def get_all_detections():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections")
    detections = cursor.fetchall()
    conn.close()

    return JSONResponse({
        "detections": [dict(d) for d in detections]
    })

@app.get("/detection/{id}")
async def get_detection(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM detections WHERE id = ?",
        (id,)
    )
    detection = cursor.fetchone()
    conn.close()

    if detection is None:
        raise HTTPException(
            status_code=404,
            detail="Detection not found"
        )
    
    image_path = detection["image_path"]
    detection_data = json.loads(
        detection["detection_data"]
    )
    
    def image_stream():
        with open(image_path, "rb") as image_file:
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