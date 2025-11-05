import requests
import cv2
import json

log_file = "/app/output/detections.log"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")

url = "http://yolov8_server:5000/detect"
image_path = "test.jpg"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

print(f"{type(response)} \n {response}")

if response.status_code == 200:
    data = response.json()
    detections = data["detection"]
    id = data["id"]

else:
    print("Error:", response.status_code, response.text)
    detections = []

log(f"Data type: {type(detections)}, Detections: {detections}")
print(f"id: {id}")

img = cv2.imread(image_path)

for det in detections:
    box = det["box"]
    x1, y1 = int(box["x1"]), int(box["y1"])
    x2, y2 = int(box["x2"]), int(box["y2"])
    label = f"{det['name']} {det['confidence']:.2f}"

    # Draw rectangle
    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    # Draw label background
    (w, h), _ = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        1
    )
    cv2.rectangle(
        img,
        (x1, y1 - 20),
        (x1 + w, y1),
        (0, 255, 0),
        -1
    )

    # Put label text
    cv2.putText(
        img,
        label,
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 0),
        1
    )

output_path = "/app/output/output_with_boxes.jpg"
cv2.imwrite(output_path, img)
log(f"Saved detections to {output_path}")
