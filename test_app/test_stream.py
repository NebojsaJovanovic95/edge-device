import requests

SERVER_URL = "http://yolov8_server:5000"
TEST_IMAGE = "test.jpg"

def run_test():
    with open(TEST_IMAGE, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{SERVER_URL}/stream", files=files)
    
    print("Status code:", response.status_code)
    print("Response:", response.json())
