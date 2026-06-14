from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from modules.pir_sensor import PIRSensor

pir = PIRSensor(warmup=False)
print("PIR test: move in front of the sensor. Ctrl+C to stop.")
try:
    while True:
        print("motion=", pir.motion_detected())
        time.sleep(0.5)
except KeyboardInterrupt:
    pir.close()
