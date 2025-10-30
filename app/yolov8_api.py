from ultralytics import YOLO
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import tempfile, os

app = FastAPI(title="YOLOv8 Edge API")

model = YOLO("/models/yolov8n.pt")

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    results = model(tmp_path)
    os.remove(tmp_path)

    return JSONResponse(results[0].tojson())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
