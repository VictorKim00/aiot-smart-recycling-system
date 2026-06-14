from __future__ import annotations

import time
import config

try:
    from gpiozero import PWMOutputDevice
except Exception:  # pragma: no cover
    PWMOutputDevice = None


class ServoController:
    """Controls one cleaning brush servo/motor trigger.

    Final demo behavior:
        - plastic detected -> cleaning brush rotates for 10 seconds
        - can/paper detected -> no motor action

    Hardware notes:
        - Signal wire -> GPIO18 physical pin 12 by default
        - Servo VCC -> external 5V power +
        - Servo GND -> external power GND
        - Raspberry Pi GND -> same external power GND
        - For continuous rotation, use a 360-degree servo or DC motor driver.
    """

    def __init__(self):
        self.enabled = bool(getattr(config, "SERVO_ENABLED", False))
        self.pin = int(getattr(config, "CLEANING_SERVO_PIN", 18))
        self.run_seconds = float(getattr(config, "CLEANING_SERVO_RUN_SECONDS", 10))
        self.stop_duty = float(getattr(config, "CLEANING_SERVO_STOP_DUTY", 7.5))
        self.run_duty = float(getattr(config, "CLEANING_SERVO_RUN_DUTY", 10.0))
        self.pwm = None

        if not self.enabled:
            print("[Servo] Disabled")
            return

        if PWMOutputDevice is None:
            print("[Servo] gpiozero PWMOutputDevice unavailable. Simulation mode.")
            return

        try:
            self.pwm = PWMOutputDevice(
                self.pin,
                frequency=50,
                initial_value=self.stop_duty / 100.0,
            )
            print(f"[Servo] Cleaning servo ready on GPIO{self.pin}")
        except Exception as exc:
            print(f"[Servo] Hardware init failed: {exc}")
            print("[Servo] Simulation mode")
            self.pwm = None

    def _set_duty(self, duty_percent: float) -> None:
        if self.pwm is None:
            print(f"[Servo] SIM duty={duty_percent}%")
            return
        self.pwm.value = max(0.0, min(1.0, duty_percent / 100.0))

    def stop(self) -> None:
        self._set_duty(self.stop_duty)
        time.sleep(0.2)
        # Detach-like behavior to reduce jitter after stop.
        if self.pwm is not None:
            self.pwm.value = 0

    def run_cleaning_brush(self) -> bool:
        if not self.enabled:
            print("[Servo] Disabled. Cleaning skipped.")
            return False

        print(f"[Servo] Cleaning brush ON for {self.run_seconds:.1f} seconds")
        self._set_duty(self.run_duty)
        time.sleep(self.run_seconds)
        print("[Servo] Cleaning brush OFF")
        self.stop()
        return self.pwm is not None

    def open_category(self, category: str, hold: float | None = None) -> bool:
        """Backward-compatible method name used by main.py.

        The original code opened a category-specific lid. Final code uses the
        same call site but maps only plastic to cleaning-brush activation.
        """
        category = str(category).lower()

        if not self.enabled:
            print(f"[Servo] Disabled. Skip category={category}")
            return False

        if category == "plastic":
            return self.run_cleaning_brush()

        print(f"[Servo] No cleaning action for category={category}")
        return False

    def close(self) -> None:
        self.stop()
        if self.pwm is not None:
            try:
                self.pwm.close()
            except Exception:
                pass
