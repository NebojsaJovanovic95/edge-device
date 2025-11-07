import cv2
from typing import Any

log_file = "/app/output/detections.log"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")

def draw_detection(
    image_path: str,
    detections: list[dict[str, Any]]
) -> None:
    img = cv2.imread(image_path)

    for det in detections:
        box = det["box"]
        x1, y1 = int(box["x1"]), int(box["y1"])
        x2, y2 = int(box["x2"]), int(box["y2"])
        label = f"{det['name']} {det['confidence']:.2f}"

        # Draw rectangle
        cv2.rectangle(
            img,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # Draw label background
        (w, h), _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            1
        )
        cv2.rectangle(
            img,
            (x1, y1 - 20),
            (x1 + w, y1),
            (0, 255, 0),
            -1
        )

        # Put label text
        cv2.putText(
            img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1
        )

    output_path = "/app/output/output_with_boxes.jpg"
    cv2.imwrite(output_path, img)
    log(f"Saved detections to {output_path}")