from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
import config

FIELDNAMES = [
    "timestamp",
    "event_type",
    "status",
    "label",
    "category",
    "confidence",
    "temperature_c",
    "humidity_percent",
    "fullness_sensor",
    "distance_cm",
    "fullness_percent",
    "image_path",
    "annotated_path",
    "note",
]


class EventLogger:
    def __init__(self):
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        config.ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
        self.csv_path = Path(config.LOG_CSV)
        self.stats_path = Path(config.STATS_JSON)
        self._ensure_csv_header()
        self.stats = self._load_stats()

    def _ensure_csv_header(self) -> None:
        if self.csv_path.exists() and self.csv_path.stat().st_size > 0:
            return
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

    def _load_stats(self) -> dict[str, int]:
        if self.stats_path.exists():
            try:
                with self.stats_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "plastic": 0,
            "can": 0,
            "paper": 0,
            "unknown": 0,
            "uncertain": 0,
            "no_detection": 0,
            "env_log": 0,
        }

    def _save_stats(self) -> None:
        with self.stats_path.open("w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def log(self, row: dict) -> dict:
        complete = {field: "" for field in FIELDNAMES}
        complete.update(row)
        complete["timestamp"] = complete.get("timestamp") or datetime.now().isoformat(timespec="seconds")

        with self.csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(complete)

        self._update_stats(complete)
        return complete

    def _update_stats(self, row: dict) -> None:
        if row.get("event_type") == "environment":
            self.stats["env_log"] = self.stats.get("env_log", 0) + 1
        elif row.get("status") == "ok":
            category = row.get("category") or "unknown"
            self.stats[category] = self.stats.get(category, 0) + 1
        elif row.get("status") == "uncertain":
            self.stats["uncertain"] = self.stats.get("uncertain", 0) + 1
        else:
            self.stats["no_detection"] = self.stats.get("no_detection", 0) + 1
        self._save_stats()
