from __future__ import annotations

import statistics
import time
import config

try:
    from gpiozero import DigitalInputDevice, DigitalOutputDevice
except Exception:  # pragma: no cover
    DigitalInputDevice = None
    DigitalOutputDevice = None


class UltrasonicSensor:
    """HC-SR04 distance sensor using trigger/echo pins.

    Important hardware note:
    HC-SR04 ECHO output is usually 5V. Raspberry Pi GPIO is 3.3V-only.
    Use a voltage divider or level shifter on ECHO before connecting to GPIO.
    """

    SPEED_OF_SOUND_CM_PER_SEC = 34300.0

    def __init__(self, name: str, trigger_pin: int, echo_pin: int):
        self.name = name
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.trigger = None
        self.echo = None

        if DigitalOutputDevice is None or DigitalInputDevice is None:
            print(f"[Ultrasonic:{self.name}] gpiozero not available. Simulation mode.")
            return

        try:
            self.trigger = DigitalOutputDevice(self.trigger_pin, initial_value=False)
            self.echo = DigitalInputDevice(self.echo_pin, pull_up=False)
            time.sleep(0.05)
        except Exception as exc:
            print(f"[Ultrasonic:{self.name}] Hardware init failed: {exc}. Simulation mode.")
            self.trigger = None
            self.echo = None

    @property
    def available(self) -> bool:
        return self.trigger is not None and self.echo is not None

    def read_distance_cm_once(self) -> float | None:
        if not self.available:
            return None

        timeout = config.ULTRASONIC_TIMEOUT_SECONDS

        # Ensure clean low pulse.
        self.trigger.off()
        time.sleep(0.000002)

        # 10us trigger pulse.
        self.trigger.on()
        time.sleep(0.00001)
        self.trigger.off()

        start_wait = time.monotonic()
        while self.echo.value == 0:
            if time.monotonic() - start_wait > timeout:
                return None
        pulse_start = time.monotonic()

        while self.echo.value == 1:
            if time.monotonic() - pulse_start > timeout:
                return None
        pulse_end = time.monotonic()

        pulse_duration = pulse_end - pulse_start
        distance_cm = (pulse_duration * self.SPEED_OF_SOUND_CM_PER_SEC) / 2.0

        if distance_cm <= 0 or distance_cm > config.ULTRASONIC_MAX_DISTANCE_CM:
            return None
        return distance_cm

    def read_distance_cm(self, samples: int | None = None) -> float | None:
        samples = config.ULTRASONIC_SAMPLES if samples is None else samples
        values = []
        for _ in range(samples):
            d = self.read_distance_cm_once()
            if d is not None:
                values.append(d)
            time.sleep(0.05)

        if not values:
            return None
        return float(statistics.median(values))

    def close(self) -> None:
        for dev in (self.trigger, self.echo):
            if dev is not None:
                try:
                    dev.close()
                except Exception:
                    pass
