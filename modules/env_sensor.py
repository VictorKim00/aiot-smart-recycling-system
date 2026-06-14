from __future__ import annotations

import time
import config

try:
    import board
    import adafruit_dht
except Exception:  # pragma: no cover
    board = None
    adafruit_dht = None


class EnvSensor:
    """DHT11/DHT22 temperature and humidity reader."""

    def __init__(self):
        self.enabled = config.ENV_ENABLED
        self.device = None
        self.last_temp: float | None = None
        self.last_humidity: float | None = None
        self.last_read_time = 0.0

        if not self.enabled:
            return

        if board is None or adafruit_dht is None:
            print("[ENV] adafruit_dht not available. Environment readings disabled.")
            return

        try:
            pin_obj = getattr(board, f"D{config.DHT_PIN}")
            sensor_class = adafruit_dht.DHT22 if config.DHT_TYPE.upper() == "DHT22" else adafruit_dht.DHT11
            self.device = sensor_class(pin_obj)
        except Exception as exc:
            print(f"[ENV] Init failed: {exc}. Environment readings disabled.")
            self.device = None

    def read(self) -> tuple[float | None, float | None]:
        if self.device is None:
            return self.last_temp, self.last_humidity

        try:
            temp = self.device.temperature
            humidity = self.device.humidity
            if temp is not None:
                self.last_temp = round(float(temp), 1)
            if humidity is not None:
                self.last_humidity = round(float(humidity), 1)
            self.last_read_time = time.monotonic()
        except RuntimeError:
            # DHT sensors often fail occasional reads; keep cached values.
            pass
        except Exception as exc:
            print(f"[ENV] Read failed: {exc}")
        return self.last_temp, self.last_humidity

    def read_cached(self) -> tuple[float | None, float | None]:
        if time.monotonic() - self.last_read_time > 2.5:
            return self.read()
        return self.last_temp, self.last_humidity

    def close(self) -> None:
        if self.device is not None:
            try:
                self.device.exit()
            except Exception:
                pass
