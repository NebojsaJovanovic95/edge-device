import requests
import json

url_all = "http://yolov8_server:5000/detections"

response = requests.get(url_all)

if response.status_code == 200:
    data = response.json()
    print("All detections:", json.dumps(data, indent=2))
else:
    print("Error fetching detections:", response.status_code, response.text)
