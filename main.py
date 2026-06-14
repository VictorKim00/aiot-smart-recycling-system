from __future__ import annotations

import select
import sys
import time
import traceback
import config
from modules.camera_source import CameraSource
from modules.cloud_sync import CloudSync
from modules.env_sensor import EnvSensor
from modules.event_logger import EventLogger
from modules.fullness_monitor import FullnessMonitor
from modules.lcd_display import LCDDisplay
from modules.pir_sensor import PIRSensor
from modules.servo_controller import ServoController
from modules.waste_rules import lcd_lines_for_detection, lcd_lines_for_uncertain
from modules.yolo_detector import YOLODetector, DetectionResult


class SmartRecyclingSystem:
    def __init__(self):
        self.running = True
        self.last_idle_lcd = 0.0
        self.last_env_log = 0.0
        self.last_fullness_idle = 0.0
        self.cached_fullness: dict[str, dict[str, float | None]] = {}

        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        config.ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
        config.CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)

        self.lcd = LCDDisplay()
        self.logger = EventLogger()
        self.cloud = CloudSync()
        self.env = EnvSensor()
        self.fullness = FullnessMonitor()
        self.servo = ServoController()
        self.pir = PIRSensor(warmup=config.PIR_ENABLED)

        self.lcd.show_lines(["Smart Recycling", "Loading camera", "and YOLO..."], hold=1)
        self.camera = CameraSource()
        self.yolo = YOLODetector()
        self.lcd.show_lines(["Smart Recycling", "System Ready", "Waiting motion"], hold=1)

    def manual_enter_triggered(self) -> bool:
        """Development fallback when PIR hardware is not connected.

        Run main.py from a terminal and press Enter to trigger detection.
        """
        if not config.SIMULATION_WHEN_HARDWARE_MISSING:
            return False
        if not sys.stdin.isatty():
            return False
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if ready:
            sys.stdin.readline()
            return True
        return False

    def update_idle_display_and_logs(self) -> None:
        now = time.monotonic()

        temp_c, humidity = self.env.read_cached()

        if now - self.last_fullness_idle >= config.FULLNESS_IDLE_INTERVAL:
            self.cached_fullness = self.fullness.read_all()
            self.last_fullness_idle = now

        if now - self.last_idle_lcd >= config.IDLE_LCD_INTERVAL:
            fullness_line = "Full: --"
            if self.cached_fullness:
                # Show first sensor on idle screen.
                first_name = next(iter(self.cached_fullness.keys()))
                fp = self.cached_fullness[first_name].get("fullness_percent")
                fullness_line = f"{first_name} Full:{fp:.0f}%" if fp is not None else f"{first_name} Full:--"

            temp_line = f"Temp:{temp_c:.1f}C" if temp_c is not None else "Temp:--"
            hum_line = f"Hum:{humidity:.1f}%" if humidity is not None else "Hum:--"
            self.lcd.show_lines([
                "Smart Recycle Ready",
                f"{temp_line} {hum_line}"[: config.LCD_COLS],
                fullness_line,
                "Move item near PIR",
            ])
            self.last_idle_lcd = now

        if now - self.last_env_log >= config.ENV_LOG_INTERVAL:
            first_sensor = ""
            first_distance = ""
            first_fullness = ""
            if self.cached_fullness:
                first_sensor = next(iter(self.cached_fullness.keys()))
                first_distance = self.cached_fullness[first_sensor].get("distance_cm") or ""
                first_fullness = self.cached_fullness[first_sensor].get("fullness_percent") or ""
            row = self.logger.log({
                "event_type": "environment",
                "status": "idle",
                "temperature_c": temp_c if temp_c is not None else "",
                "humidity_percent": humidity if humidity is not None else "",
                "fullness_sensor": first_sensor,
                "distance_cm": first_distance,
                "fullness_percent": first_fullness,
                "note": "Idle environment tracking",
            })
            self.cloud.send(row)
            self.last_env_log = now

    def classify_with_retries(self) -> tuple[DetectionResult, object, object]:
        best_detection = DetectionResult(status="no_detection")
        best_frame = None
        best_annotated = None

        for attempt in range(1, config.DETECTION_TRIES + 1):
            self.lcd.show_lines(["Capturing item", f"Try {attempt}/{config.DETECTION_TRIES}"], hold=0.2)
            frame = self.camera.capture_frame()
            detection, annotated = self.yolo.detect_with_annotated(frame)

            print(f"[Detect] attempt={attempt}, result={detection}")

            if best_frame is None or detection.confidence >= best_detection.confidence:
                best_detection = detection
                best_frame = frame
                best_annotated = annotated

            if detection.status == "ok":
                break
            time.sleep(0.4)

        return best_detection, best_frame, best_annotated

    def handle_motion_event(self) -> None:
        self.lcd.show_lines(["Motion detected", "Please hold item", "in camera zone"], hold=0.8)

        try:
            detection, frame, annotated = self.classify_with_retries()
        except Exception as exc:
            print("[System] Camera/YOLO error:", exc)
            traceback.print_exc()
            self.lcd.show_lines(["Camera/YOLO Error", "Check terminal"], hold=3)
            return

        if frame is None:
            self.lcd.show_lines(["No image captured", "Try again"], hold=3)
            return

        image_path = CameraSource.save_frame(frame, config.IMAGE_DIR, prefix="waste")
        annotated_path = CameraSource.save_frame(annotated if annotated is not None else frame, config.ANNOTATED_DIR, prefix="annotated")

        temp_c, humidity = self.env.read_cached()
        fullness_sensor = ""
        distance_cm = None
        fullness_percent = None
        servo_opened = False
        note = "PIR triggered detection"

        if detection.status == "ok":
            fullness_sensor, distance_cm, fullness_percent = self.fullness.read_for_category(detection.category)
            self.lcd.show_lines(
                lcd_lines_for_detection(detection.label, detection.category, detection.confidence, fullness_percent),
                hold=1.5,
            )

            if fullness_percent is not None and fullness_percent >= config.FULLNESS_BLOCK_OPEN_PERCENT:
                self.lcd.show_lines([
                    "Bin almost/full!",
                    f"{detection.category}:{fullness_percent:.0f}%",
                    "Action blocked",
                    "Please empty bin",
                ], hold=3)
                note = "Bin full - motor action blocked"
            else:
                servo_opened = self.servo.open_category(detection.category)
                if fullness_percent is not None and fullness_percent >= config.FULLNESS_ALERT_PERCENT:
                    if servo_opened:
                        self.lcd.show_lines([
                            "Cleaning done",
                            f"Warning Full:{fullness_percent:.0f}%",
                            "Empty soon",
                        ], hold=2)
                    else:
                        self.lcd.show_lines([
                            "Guide complete",
                            f"Warning Full:{fullness_percent:.0f}%",
                            "Dispose manually",
                        ], hold=2)
                    note = "Bin near full - action completed with warning"
                elif servo_opened:
                    self.lcd.show_lines(["Cleaning done", "Plastic brush run", "Thank you"], hold=2)
                    note = "Plastic cleaning brush activated"
                else:
                    self.lcd.show_lines(["Guide complete", "Dispose manually"], hold=2)

        elif detection.status == "uncertain":
            self.lcd.show_lines(lcd_lines_for_uncertain(detection.label, detection.confidence), hold=3)
            note = "Low confidence - retry requested"
        else:
            self.lcd.show_lines(["No waste found", "Move item closer", "Try again"], hold=3)
            note = "No detection"

        row = self.logger.log({
            "event_type": "waste_detection",
            "status": detection.status,
            "label": detection.label,
            "category": detection.category,
            "confidence": f"{detection.confidence:.4f}",
            "temperature_c": temp_c if temp_c is not None else "",
            "humidity_percent": humidity if humidity is not None else "",
            "fullness_sensor": fullness_sensor,
            "distance_cm": f"{distance_cm:.2f}" if distance_cm is not None else "",
            "fullness_percent": f"{fullness_percent:.1f}" if fullness_percent is not None else "",
            "image_path": str(image_path),
            "annotated_path": str(annotated_path),
            "note": note,
        })
        self.cloud.send(row)

    def run(self) -> None:
        print("[System] Running. Press Ctrl+C to stop. Press Enter to trigger manually if PIR is unavailable.")
        try:
            while self.running:
                if self.pir.motion_detected() or self.manual_enter_triggered():
                    self.handle_motion_event()
                    time.sleep(config.PIR_COOLDOWN_SECONDS)
                    continue

                self.update_idle_display_and_logs()
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\n[System] Stopping...")
        finally:
            self.close()

    def close(self) -> None:
        for obj in (self.pir, self.camera, self.servo, self.fullness, self.env, self.lcd):
            try:
                obj.close()
            except Exception:
                pass


if __name__ == "__main__":
    system = SmartRecyclingSystem()
    system.run()
