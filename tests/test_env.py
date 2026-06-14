from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from modules.env_sensor import EnvSensor

env = EnvSensor()
try:
    for _ in range(10):
        temp, hum = env.read()
        print(f"temperature={temp}, humidity={hum}")
        time.sleep(2.5)
finally:
    env.close()
