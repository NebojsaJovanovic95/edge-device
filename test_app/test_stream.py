import requests

url_stream = "http://yolov8_server:5000/stream"
image_path = "test.jpg"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url_stream, files=files)

print(response.status_code, response.json())
