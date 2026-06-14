from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.servo_controller import ServoController

servo = ServoController()
try:
    print("Testing plastic cleaning brush action")
    servo.open_category("plastic")

    print("Testing can/paper should not run motor")
    servo.open_category("can")
    servo.open_category("paper")
finally:
    servo.close()
