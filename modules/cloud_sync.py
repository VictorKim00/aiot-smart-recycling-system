from __future__ import annotations

import json
import urllib.parse
import urllib.request
import config


class CloudSync:
    """Optional dashboard sync to Google Sheets Apps Script or Firebase Realtime DB.

    Mobile alerts are intentionally excluded.
    """

    def __init__(self):
        self.enabled = config.CLOUD_ENABLED
        self.mode = config.CLOUD_MODE.lower()

    def send(self, row: dict) -> bool:
        if not self.enabled:
            return False
        try:
            if self.mode == "sheets":
                return self._send_sheets(row)
            if self.mode == "firebase":
                return self._send_firebase(row)
            print(f"[Cloud] Unknown CLOUD_MODE: {config.CLOUD_MODE}")
            return False
        except Exception as exc:
            print(f"[Cloud] Sync failed: {exc}")
            return False

    def _send_sheets(self, row: dict) -> bool:
        if not config.SHEETS_WEBAPP_URL:
            return False
        body = json.dumps(row).encode("utf-8")
        req = urllib.request.Request(
            config.SHEETS_WEBAPP_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300

    def _send_firebase(self, row: dict) -> bool:
        if not config.FIREBASE_DB_URL:
            return False
        base = config.FIREBASE_DB_URL.rstrip("/")
        url = f"{base}/events.json"
        if config.FIREBASE_AUTH_TOKEN:
            url += "?" + urllib.parse.urlencode({"auth": config.FIREBASE_AUTH_TOKEN})
        body = json.dumps(row).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
