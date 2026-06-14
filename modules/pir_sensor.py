from __future__ import annotations

import time
import config

try:
    from gpiozero import MotionSensor, DigitalInputDevice
except Exception:  # pragma: no cover - only used on non-Pi development machines
    MotionSensor = None
    DigitalInputDevice = None


class PIRSensor:
    """PIR motion sensor used as a wake-up trigger for the camera."""

    def __init__(self, pin: int | None = None, warmup: bool = True):
        self.pin = config.PIR_PIN if pin is None else pin
        self.device = None
        self.fake_state = False
        self.enabled = config.PIR_ENABLED

        if not self.enabled:
            return

        if MotionSensor is not None:
            try:
                self.device = MotionSensor(self.pin)
            except Exception:
                # Some PIR modules work better as a simple digital input.
                try:
                    self.device = DigitalInputDevice(self.pin)
                except Exception:
                    self.device = None

        if warmup and self.device is not None:
            print(f"[PIR] Warming up for {config.PIR_WARMUP_SECONDS}s...")
            time.sleep(config.PIR_WARMUP_SECONDS)

        if self.device is None:
            print("[PIR] Hardware not available. Simulation mode: press Enter in main loop if enabled.")

    def motion_detected(self) -> bool:
        if not self.enabled:
            return True
        if self.device is None:
            return False
        if hasattr(self.device, "motion_detected"):
            return bool(self.device.motion_detected)
        if hasattr(self.device, "value"):
            return bool(self.device.value)
        return False

    def close(self) -> None:
        if self.device is not None:
            try:
                self.device.close()
            except Exception:
                pass
