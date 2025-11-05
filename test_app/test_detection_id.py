import requests
import json

detection_id = 1  # Replace with an actual detection ID
url_single = f"http://yolov8_server:5000/detection/{detection_id}"

response = requests.get(url_single, stream=True)

if response.status_code == 200:
    # Save the image returned
    with open("detection_image.jpg", "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    
    # Get the detection data from header
    detection_data = json.loads(response.headers["X-Detection-Data"])
    print(f"Detection {detection_id} data:", json.dumps(detection_data, indent=2))
else:
    print(f"Detection {detection_id} not found:", response.status_code)
