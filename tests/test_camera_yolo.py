from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import config
from modules.camera_source import CameraSource
from modules.yolo_detector import YOLODetector

camera = CameraSource()
detector = YOLODetector()
try:
    frame = camera.capture_frame()
    detection, annotated = detector.detect_with_annotated(frame)
    print(detection)
    out = config.DATA_DIR / "test_camera_yolo_result.jpg"
    cv2.imwrite(str(out), annotated)
    print("saved:", out)
finally:
    camera.close()
