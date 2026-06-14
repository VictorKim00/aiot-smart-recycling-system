from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
import cv2
import config


class CameraSource:
    """Camera wrapper supporting Picamera2 first, OpenCV fallback second."""

    def __init__(self):
        self.backend = None
        self.picam2 = None
        self.cap = None
        desired = config.CAMERA_BACKEND.lower()

        if desired in {"auto", "picamera2"}:
            try:
                from picamera2 import Picamera2

                self.picam2 = Picamera2()
                camera_config = self.picam2.create_preview_configuration(
                    main={"size": (config.FRAME_WIDTH, config.FRAME_HEIGHT), "format": "RGB888"}
                )
                self.picam2.configure(camera_config)
                self.picam2.start()
                time.sleep(config.CAMERA_WARMUP_SECONDS)
                self.backend = "picamera2"
                print("[Camera] Using Picamera2")
                return
            except Exception as exc:
                if desired == "picamera2":
                    raise RuntimeError(f"Picamera2 requested but failed: {exc}") from exc
                print(f"[Camera] Picamera2 unavailable: {exc}. Trying OpenCV.")

        if desired in {"auto", "opencv"}:
            self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            if not self.cap.isOpened():
                raise RuntimeError("OpenCV camera could not be opened.")
            time.sleep(config.CAMERA_WARMUP_SECONDS)
            self.backend = "opencv"
            print("[Camera] Using OpenCV VideoCapture")
            return

        raise ValueError(f"Unknown CAMERA_BACKEND: {config.CAMERA_BACKEND}")

    def capture_frame(self):
        if self.backend == "picamera2":
            # Picamera2 returns RGB; convert to BGR for OpenCV and Ultralytics consistency.
            frame_rgb = self.picam2.capture_array()
            return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        if self.backend == "opencv":
            # Drop a couple frames to reduce stale/auto-exposure frames.
            frame = None
            for _ in range(3):
                ok, frame = self.cap.read()
                if not ok:
                    frame = None
                time.sleep(0.03)
            if frame is None:
                raise RuntimeError("Failed to capture frame from OpenCV camera.")
            return frame

        raise RuntimeError("Camera not initialized.")

    @staticmethod
    def save_frame(frame, directory: Path, prefix: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = directory / f"{prefix}_{timestamp}.jpg"
        cv2.imwrite(str(path), frame)
        return path

    def close(self) -> None:
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except Exception:
                pass
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
