import redis
import os
import signal
import sys

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT"))
)

# BLOCK until a camera is available
camera_id = r.blpop(os.getenv("CAMERA_QUEUE"))[1].decode()

rtsp_url = r.hget(f"camera:{camera_id}", "rtsp_url").decode()

print(f"Starting stream for {camera_id} → {rtsp_url}")

def shutdown(sig, frame):
    print("Releasing camera")
    r.lpush("cameras:pending", camera_id)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)

# START RTSP LOOP (never exit)
run_rtsp_stream(rtsp_url)
