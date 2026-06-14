from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from time import sleep
from gpiozero import PWMOutputDevice

PIN = 18
p = PWMOutputDevice(PIN, frequency=50)
try:
    for duty in [2.5, 5.0, 7.5, 10.0, 12.5]:
        print("duty", duty)
        p.value = duty / 100.0
        sleep(3)
    print("off")
    p.value = 0
finally:
    p.close()
