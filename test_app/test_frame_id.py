import requests, json, os
from util import draw_detection

SERVER_URL = "http://yolov8_server:5000"
TEST_ID = 1  # Replace with an actual frame ID returned by /detect

def run_test(id: int = TEST_ID):
    url = f"{SERVER_URL}/frame/{id}"
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return

    # 1️⃣ Parse frame metadata from header
    frame_header = response.headers.get("X-Detection-Data", "[]")
    frames = json.loads(frame_header)
    print(f"frames {type(frames)} after json loads {frames}")

    # 2️⃣ Save streamed image temporarily to disk
    os.makedirs("/app/output", exist_ok=True)
    image_path = f"/app/output/frame_raw_{id}.jpg"
    output_path = f"/app/output/frame_id_{id}.jpg"

    with open(image_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    # Draw frame
    draw_detection(image_path, frames, output_path)
