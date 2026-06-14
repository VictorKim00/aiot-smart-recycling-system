from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from modules.fullness_monitor import FullnessMonitor

fullness = FullnessMonitor()
print("Fullness test. Ctrl+C to stop.")
try:
    while True:
        print(fullness.read_all())
        time.sleep(1)
except KeyboardInterrupt:
    fullness.close()
