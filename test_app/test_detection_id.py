import requests

SERVER_URL = "http://yolov8_server:5000"
TEST_ID = 1  # Replace with an actual detection ID returned by /detect

def run_test(id: int = TEST_ID):
    url = f"{SERVER_URL}/detection/{id}"
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    # 1️⃣ Parse detection metadata from header
    detection_header = response.headers.get("X-Detection-Data", "[]")
    detections = json.loads(detection_header)

    # 2️⃣ Save streamed image temporarily to disk
    os.makedirs("/app/output", exist_ok=True)
    image_path = "/app/output/detection_raw.jpg"

    with open(image_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    # 3️⃣ Draw detections using your existing utility
    draw_detection(image_path, detections)
