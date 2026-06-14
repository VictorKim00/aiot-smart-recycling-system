from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import config
from modules.ultrasonic import UltrasonicSensor

print("HC-SR04 ultrasonic distance test")
print("IMPORTANT: ECHO must go through voltage divider/level shifter to 3.3V.")

sensors = []
for name, pins in config.FULLNESS_SENSORS.items():
    sensors.append(UltrasonicSensor(name, pins["trigger"], pins["echo"]))

try:
    while True:
        for sensor in sensors:
            print(sensor.name, "distance_cm=", sensor.read_distance_cm())
        print("---")
        time.sleep(1)
except KeyboardInterrupt:
    for sensor in sensors:
        sensor.close()
