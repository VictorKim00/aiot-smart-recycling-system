from __future__ import annotations

import json
import time
from pathlib import Path
import config
from modules.ultrasonic import UltrasonicSensor


class FullnessMonitor:
    """Estimate bin fullness from ultrasonic distance.

    Formula:
        fullness % = (empty_distance - current_distance) / (empty_distance - full_distance) * 100

    Example:
        sensor at top of bin, empty distance = 35 cm, full distance = 6 cm.
        If current distance is 20 cm, fullness = about 52%.
    """

    def __init__(self):
        self.enabled = config.FULLNESS_ENABLED
        self.sensors: dict[str, UltrasonicSensor] = {}
        self.calibration: dict[str, dict[str, float]] = {}
        self.last_values: dict[str, float | None] = {}
        self.last_read_time = 0.0

        if not self.enabled:
            return

        for name, pins in config.FULLNESS_SENSORS.items():
            self.sensors[name] = UltrasonicSensor(
                name=name,
                trigger_pin=int(pins["trigger"]),
                echo_pin=int(pins["echo"]),
            )

        self.calibration = self._load_calibration()

    def _load_calibration(self) -> dict[str, dict[str, float]]:
        path = Path(config.FULLNESS_CALIBRATION_FILE)
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as exc:
                print(f"[Fullness] Failed to load calibration: {exc}")

        return {
            name: {
                "empty_cm": float(config.DEFAULT_EMPTY_DISTANCE_CM),
                "full_cm": float(config.DEFAULT_FULL_DISTANCE_CM),
            }
            for name in config.FULLNESS_SENSORS.keys()
        }

    def save_calibration(self) -> None:
        Path(config.CALIBRATION_DIR).mkdir(parents=True, exist_ok=True)
        with Path(config.FULLNESS_CALIBRATION_FILE).open("w", encoding="utf-8") as f:
            json.dump(self.calibration, f, indent=2, ensure_ascii=False)

    def calibrate_empty(self, samples: int = 10) -> dict[str, float | None]:
        measured: dict[str, float | None] = {}
        for name, sensor in self.sensors.items():
            distances = []
            for _ in range(samples):
                d = sensor.read_distance_cm()
                if d is not None:
                    distances.append(d)
                time.sleep(0.1)

            if distances:
                avg = sum(distances) / len(distances)
                self.calibration.setdefault(name, {})["empty_cm"] = round(avg, 2)
                self.calibration.setdefault(name, {})["full_cm"] = float(config.DEFAULT_FULL_DISTANCE_CM)
                measured[name] = round(avg, 2)
            else:
                measured[name] = None
        self.save_calibration()
        return measured

    def calibrate_full(self, full_distance_cm: float | None = None, samples: int = 10) -> dict[str, float | None]:
        """Optional: measure or set the distance considered as full.

        If full_distance_cm is provided, the same value is applied to all sensors.
        Otherwise, the current measured distances are saved as full_cm.
        """
        measured: dict[str, float | None] = {}
        for name, sensor in self.sensors.items():
            if full_distance_cm is not None:
                self.calibration.setdefault(name, {})["full_cm"] = float(full_distance_cm)
                measured[name] = float(full_distance_cm)
                continue

            distances = []
            for _ in range(samples):
                d = sensor.read_distance_cm()
                if d is not None:
                    distances.append(d)
                time.sleep(0.1)
            if distances:
                avg = sum(distances) / len(distances)
                self.calibration.setdefault(name, {})["full_cm"] = round(avg, 2)
                measured[name] = round(avg, 2)
            else:
                measured[name] = None
        self.save_calibration()
        return measured

    def distance_to_percent(self, sensor_name: str, distance_cm: float | None) -> float | None:
        if distance_cm is None:
            return None
        cal = self.calibration.get(sensor_name, {})
        empty_cm = float(cal.get("empty_cm", config.DEFAULT_EMPTY_DISTANCE_CM))
        full_cm = float(cal.get("full_cm", config.DEFAULT_FULL_DISTANCE_CM))

        if empty_cm <= full_cm:
            return None

        percent = (empty_cm - distance_cm) / (empty_cm - full_cm) * 100.0
        return max(0.0, min(100.0, percent))

    def read_sensor(self, sensor_name: str) -> tuple[float | None, float | None]:
        if not self.enabled:
            return None, None
        sensor = self.sensors.get(sensor_name)
        if sensor is None:
            return None, None
        distance_cm = sensor.read_distance_cm()
        percent = self.distance_to_percent(sensor_name, distance_cm)
        self.last_values[sensor_name] = percent
        self.last_read_time = time.monotonic()
        return distance_cm, percent

    def read_all(self) -> dict[str, dict[str, float | None]]:
        results: dict[str, dict[str, float | None]] = {}
        if not self.enabled:
            return results
        for name in self.sensors.keys():
            distance_cm, percent = self.read_sensor(name)
            results[name] = {
                "distance_cm": None if distance_cm is None else round(distance_cm, 2),
                "fullness_percent": None if percent is None else round(percent, 1),
            }
        return results

    def category_sensor_name(self, category: str) -> str:
        return config.CATEGORY_TO_FULLNESS_SENSOR.get(category, "main")

    def read_for_category(self, category: str) -> tuple[str, float | None, float | None]:
        sensor_name = self.category_sensor_name(category)
        distance_cm, percent = self.read_sensor(sensor_name)
        return sensor_name, distance_cm, percent

    def close(self) -> None:
        for sensor in self.sensors.values():
            sensor.close()
