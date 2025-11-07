import requests

SERVER_URL = "http://yolov8_server:5000"
TEST_ID = 1  # Replace with an actual detection ID returned by /detect

def run_test(id: int = TEST_ID):
    response = requests.get(f"{SERVER_URL}/detection/{id}")
    print("Status code:", response.status_code)
    if response.status_code == 200:
        with open("output_test.jpg", "wb") as f:
            f.write(response.content)
        print("X-Detection-Data:", response.headers.get("X-Detection-Data"))
    else:
        print("Error response:", response.text)
