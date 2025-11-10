import requests
import json

from util import draw_detection

log_file = "/app/output/detections.log"
url = "http://yolov8_server:5000/detect"
image_path = "test.jpg"
def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")

def run_test():
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
        id = -1

    draw_detection(
        image_path="test.jpg",
        detections=detections
    )

    return id