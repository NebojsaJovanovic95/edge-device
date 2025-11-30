import requests

SERVER_URL = "http://yolov8_server:5000"
TEST_IMAGE = "test.jpg"

def run_test():
    response = requests.get(f"{SERVER_URL}/detections")
    
    print("Status code:", response.status_code)
    print("Response:", response.json())
