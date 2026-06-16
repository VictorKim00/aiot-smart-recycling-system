"""
AIoT Smart Recycling System - FINAL CONFIG

Final demo hardware:
- Raspberry Pi 5
- PIR motion sensor: user approach trigger
- Pi Camera / USB Camera: waste image capture
- YOLOv8 custom model exported to ONNX: plastic_bottle / can / paper detection
- HC-SR04 ultrasonic sensor: bin fullness measurement
- 7-inch touch screen: large framebuffer display
- Optional cleaning brush servo: runs 10 seconds only when plastic is detected

Important:
- This final version does NOT require ultralytics or torch on Raspberry Pi.
- Put your Colab-exported ONNX model at: models/best.onnx
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
ANNOTATED_DIR = DATA_DIR / "annotated"
CALIBRATION_DIR = DATA_DIR / "calibration"
FULLNESS_CALIBRATION_FILE = CALIBRATION_DIR / "fullness_calibration.json"
LOG_CSV = DATA_DIR / "events.csv"
STATS_JSON = DATA_DIR / "stats.json"

# Custom YOLO model exported from Colab as ONNX.
# Copy best.onnx into models/best.onnx before running main.py.
MODEL_PATH = str(BASE_DIR / "models" / "best.onnx")

YOLO_IMAGE_SIZE = 640
DETECTION_CONF_THRESHOLD = 0.60
UNCERTAIN_CONF_THRESHOLD = 0.45
DETECTION_TRIES = 3

# Camera: "auto", "picamera2", or "opencv"
CAMERA_BACKEND = "auto"
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_WARMUP_SECONDS = 1.0

# PIR motion sensor for user approach / camera wake-up
PIR_ENABLED = True
PIR_PIN = 17
PIR_WARMUP_SECONDS = 30
PIR_COOLDOWN_SECONDS = 6

# DHT sensor for idle environment tracking.
# If adafruit_dht is unavailable or the sensor is not connected,
# the system continues with Temp/Hum displayed as --.
ENV_ENABLED = True
DHT_PIN = 4
DHT_TYPE = "DHT11"  # "DHT22" or "DHT11"

# 7-inch touch screen / local display output.
# This replaces the original I2C character LCD output.
LCD_ENABLED = True
DISPLAY_MODE = "framebuffer"       # final version uses /dev/fb0
SCREEN_FRAMEBUFFER = "/dev/fb0"
SCREEN_FALLBACK_TTY = "/dev/tty1"
SCREEN_HEADER = "AIoT SMART RECYCLING"

# Kept only for compatibility with older text formatting code.
LCD_COLS = 20
LCD_ROWS = 4
LCD_I2C_ADDRESS = 0x27

# Cleaning brush servo control.
# Plastic detection -> cleaning brush rotates for 10 seconds.
# For a real rotating brush, use a 360-degree continuous rotation servo
# or use a DC motor with a motor driver. A normal 180-degree servo will
# not continuously rotate.
SERVO_ENABLED = True
CLEANING_SERVO_PIN = 18             # GPIO18, physical pin 12
CLEANING_SERVO_RUN_SECONDS = 15

# Continuous rotation servo PWM duty settings.
# 7.5 is usually stop, 10.0 rotates one direction, 5.0 rotates the other.
CLEANING_SERVO_STOP_DUTY = 7.5
CLEANING_SERVO_RUN_DUTY = 10.0

# HC-SR04 ultrasonic fullness sensor.
# Mount the sensor on the lid/top of the bin facing downward.
# ECHO must be level-shifted to 3.3V before entering Raspberry Pi GPIO.
FULLNESS_ENABLED = True
FULLNESS_SENSORS = {
    "main": {"trigger": 23, "echo": 24},
}
CATEGORY_TO_FULLNESS_SENSOR = {
    "plastic": "main",
    "can": "main",
    "paper": "main",
}
DEFAULT_EMPTY_DISTANCE_CM = 35.0
DEFAULT_FULL_DISTANCE_CM = 6.0
FULLNESS_ALERT_PERCENT = 75.0
FULLNESS_BLOCK_OPEN_PERCENT = 90.0
ULTRASONIC_SAMPLES = 5
ULTRASONIC_MAX_DISTANCE_CM = 120.0
ULTRASONIC_TIMEOUT_SECONDS = 0.03

# Cloud dashboard. Mobile alert is intentionally not included.
CLOUD_ENABLED = True
CLOUD_MODE = "sheets"  # "sheets" or "firebase"
SHEETS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwCEavXqznv_RV2c_bW9-2v3gRv-SAfOdYHbb0wt8PbHKPzXTCGt0z7-_coNf78apZT/exec"
FIREBASE_DB_URL = ""
FIREBASE_AUTH_TOKEN = ""

# Idle loop timing
IDLE_LCD_INTERVAL = 3.0
ENV_LOG_INTERVAL = 10.0
FULLNESS_IDLE_INTERVAL = 5.0

# Demo/development behavior
SIMULATION_WHEN_HARDWARE_MISSING = True
