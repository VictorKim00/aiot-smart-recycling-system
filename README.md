# AIoT Smart Recycling System

**for IoT Class**

## 1. Project Overview

This project is an AIoT-based smart recycling system using Raspberry Pi 5, camera, YOLO object detection, multiple IoT sensors, LCD display, servo motor, and Google Sheets cloud dashboard.

The system detects user motion, captures a waste image, classifies the waste type using a YOLO ONNX model, displays recycling guidance on an LCD, monitors environmental data, checks bin fullness, and stores detection logs in Google Sheets.

본 프로젝트는 Raspberry Pi 5를 중심으로 카메라, YOLO 객체 인식 모델, PIR 센서, 초음파 센서, DHT11 온습도 센서, LCD, SG90 서보모터, Google Sheets 대시보드를 통합한 AIoT 스마트 분리수거 시스템이다.

---

## 2. Main Features

- Motion detection using PIR sensor
- Waste image capture using Raspberry Pi Camera
- Waste classification using YOLO ONNX model
- LCD-based recycling guidance
- Temperature and humidity monitoring using DHT11
- Bin fullness measurement using HC-SR04 ultrasonic sensor
- SG90 servo motor brush sweeping motion
- Google Sheets cloud logging
- Waste category count visualization using pie chart

---

## 3. System Flow

```text
Idle Mode
→ Display temperature, humidity, and bin status on LCD
→ Detect user motion using PIR sensor
→ Capture waste image using Raspberry Pi Camera
→ Classify waste using YOLO ONNX model
→ Display recycling guidance on LCD
→ Check bin fullness using ultrasonic sensor
→ Run SG90 servo brush sweeping motion
→ Save event log locally
→ Send recognition result to Google Sheets
→ Visualize waste count using pie chart
```

---

## 4. Hardware Components

| Component | Purpose |
|---|---|
| Raspberry Pi 5 | Main control and edge-computing hub |
| Raspberry Pi Camera | Waste image capture |
| PIR Sensor | User motion detection |
| HC-SR04 Ultrasonic Sensor | Distance and bin fullness measurement |
| DHT11 Sensor | Temperature and humidity monitoring |
| LCD Display | User guidance and system status output |
| SG90 Servo Motor | Brush sweeping motion |
| Battery Pack | External power supply for servo motor |
| Breadboard and Jumper Wires | Circuit connection |
| Wood락 Prototype Bin | Physical smart bin structure |

---

## 5. Pin Connection Summary

### SG90 Servo Motor

| Servo Pin | Connection |
|---|---|
| Signal | GPIO18, Physical Pin 12 |
| VCC | Battery Pack + |
| GND | Battery Pack - |
| Common GND | Battery Pack - connected to Raspberry Pi GND |

The SG90 servo motor is a normal angle servo, not a continuous rotation servo. Therefore, the system uses a sweeping motion instead of continuous rotation.

Servo motion:

```text
45 degrees → 135 degrees → repeat for 15 seconds → return to 90 degrees
```

---

### HC-SR04 Ultrasonic Sensor

| Sensor Pin | Raspberry Pi Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| TRIG | GPIO23, Physical Pin 16 |
| ECHO | GPIO24, Physical Pin 18 through voltage divider |

The ECHO signal must be reduced to 3.3V before entering the Raspberry Pi GPIO pin.

---

### DHT11 Temperature and Humidity Sensor

| Sensor Pin | Raspberry Pi Pin |
|---|---|
| VCC | 3.3V |
| DATA | GPIO4, Physical Pin 7 |
| GND | GND |

The DHT11 sensor is used for idle environment tracking and sanitation monitoring.

---

### PIR Motion Sensor

| Sensor Pin | Raspberry Pi Pin |
|---|---|
| VCC | 5V |
| OUT | GPIO17, Physical Pin 11 |
| GND | GND |

The PIR sensor triggers the waste classification process when user motion is detected.

---

## 6. Software Stack

- Python 3
- Raspberry Pi OS
- Picamera2
- OpenCV
- ONNX Runtime
- Adafruit DHT library
- GPIOZero
- Google Apps Script
- Google Sheets

The original YOLO `.pt` model was converted to `.onnx` to reduce storage and dependency requirements on the Raspberry Pi.

---

## 7. Project Structure

```text
aiot_recycling_ultrasonic_fullness_code/
├── main.py
├── config.py
├── models/
│   └── best.onnx
├── modules/
│   ├── camera_source.py
│   ├── cloud_sync.py
│   ├── env_sensor.py
│   ├── event_logger.py
│   ├── fullness_monitor.py
│   ├── lcd_display.py
│   ├── pir_sensor.py
│   ├── waste_rules.py
│   └── yolo_detector.py
├── tests/
│   ├── test_camera_yolo.py
│   ├── test_ultrasonic.py
│   ├── test_env.py
│   ├── test_pir.py
│   └── servo_sweep_15s.py
└── README.md
```

---

## 8. Configuration

Main configuration values are managed in `config.py`.

```python
MODEL_PATH = str(BASE_DIR / "models" / "best.onnx")

DETECTION_CONF_THRESHOLD = 0.60
UNCERTAIN_CONF_THRESHOLD = 0.45
DETECTION_TRIES = 3

PIR_ENABLED = True
PIR_PIN = 17

ENV_ENABLED = True
DHT_PIN = 4
DHT_TYPE = "DHT11"

FULLNESS_ENABLED = True
FULLNESS_SENSORS = {
    "main": {"trigger": 23, "echo": 24},
}

CLOUD_ENABLED = True
CLOUD_MODE = "sheets"
SHEETS_WEBAPP_URL = "Google Apps Script Web App URL"
```

---

## 9. How to Run

### 1. Connect to Raspberry Pi

```bash
ssh pi@raspberrypi5.local
```

### 2. Move to project directory

```bash
cd ~/aiot_recycling_ultrasonic_fullness_code
```

### 3. Activate virtual environment

```bash
source venv/bin/activate
```

### 4. Run main system

```bash
python main.py
```

To stop the system:

```text
Ctrl + C
```

---

## 10. Test Scripts

### Camera and YOLO test

```bash
python tests/test_camera_yolo.py
```

Expected result:

```text
[Camera] Using Picamera2
[YOLO] Using ONNX Runtime: models/best.onnx
DetectionResult(status='ok', label='can', category='can', confidence=...)
```

---

### Ultrasonic sensor test

```bash
python tests/test_ultrasonic.py
```

---

### DHT11 temperature and humidity test

```bash
python tests/test_env.py
```

Expected result:

```text
온도: 25.3°C, 습도: 64%
```

---

### PIR sensor test

```bash
python tests/test_pir.py
```

---

### Servo motor test

```bash
python tests/servo_sweep_15s.py
```

---

## 11. YOLO Detection Logic

The system uses an ONNX-based YOLO detector to classify waste objects.

Confidence thresholds:

```python
DETECTION_CONF_THRESHOLD = 0.60
UNCERTAIN_CONF_THRESHOLD = 0.45
```

Detection result behavior:

| Confidence Range | Result |
|---|---|
| 0.60 or higher | Accepted detection |
| 0.45 ~ 0.60 | Uncertain |
| Below 0.45 | Ignored or no detection |

To reduce false detection, the camera view was cleaned so that jumper wires, breadboard, Raspberry Pi parts, and background objects are not visible in the camera frame.

---

## 12. Servo Brush Logic

The SG90 servo motor is used as a brush-sweeping mechanism.

The brush only runs when the detected object is a plastic-related category and the confidence is high enough.

Plastic-related keywords:

```python
PLASTIC_KEYWORDS = ("plastic", "pet", "bottle")
```

Brush behavior:

```text
If detected category is plastic-related
and confidence is above threshold
→ Run SG90 sweeping motion for 15 seconds
```

Servo motion:

```text
45° → 135° → repeat → 90° center position
```

---

## 13. LCD Output

The LCD displays system status, environmental values, and recycling guidance.

Example idle screen:

```text
Smart Recycle Ready
Temp:25.3C Hum:64.0%
main Full:--
Move item near PIR
```

Example detection screen:

```text
Detected: Plastic
Category: Plastic
Confidence: 0.72
Brush running
```

---

## 14. Google Sheets Cloud Dashboard

This project includes a cloud dashboard using Google Sheets and Google Apps Script.

When an event occurs, Raspberry Pi sends detection data to a Google Apps Script Web App URL. The data is automatically appended to Google Sheets.

### Data Fields

| Field | Description |
|---|---|
| timestamp | Event time |
| event_type | Event type |
| status | Detection status |
| label | YOLO label |
| category | Waste category |
| confidence | Detection confidence |
| temperature_c | Temperature |
| humidity_percent | Humidity |
| fullness_sensor | Ultrasonic sensor name |
| distance_cm | Measured distance |
| fullness_percent | Bin fullness percentage |
| image_path | Captured image path |
| annotated_path | Annotated image path |
| note | Event note |

### Dashboard Visualization

The Google Sheet also provides a count dashboard using category data.

Example count table:

| Category | Count |
|---|---:|
| Plastic | 8 |
| Can | 4 |
| Paper | 3 |

A pie chart is used to visualize the ratio of detected waste categories.

This feature expands the system from a local IoT prototype to a data-driven AIoT recycling monitoring system.

---

## 15. Problems and Solutions

| Problem | Cause | Solution |
|---|---|---|
| `ultralytics` was too large | PyTorch dependency required too much storage | Converted YOLO `.pt` model to `.onnx` |
| `onnxruntime` not found | Python was executed outside virtual environment | Activated `venv` before running |
| Camera fallback failed | Picamera2 was not visible in normal venv | Recreated venv with `--system-site-packages` |
| Ultrasonic returned `None` | Power pin was not connected correctly | Reconnected VCC and GND |
| GPIO busy error | Previous Python process was using GPIO | Killed old process |
| DHT11 not found | Sensor pin labels were different | Rechecked actual sensor labels and rewired |
| SG90 did not rotate continuously | SG90 is not a continuous rotation servo | Implemented 15-second sweeping motion |
| False plastic detection | Jumper wires were visible to the camera | Cleaned camera view and fixed object zone |

---

## 16. Current Implementation Status

Completed:

- Raspberry Pi Camera integration
- YOLO ONNX inference
- PIR motion detection
- HC-SR04 ultrasonic distance measurement
- DHT11 temperature and humidity monitoring
- LCD output
- SG90 servo brush motion
- Google Sheets logging
- Pie chart count visualization
- Main system integration

---

## 17. Demo Scenario

1. LCD shows idle status with temperature and humidity.
2. User approaches the smart bin.
3. PIR sensor detects motion.
4. Camera captures the waste object.
5. YOLO model classifies the waste.
6. LCD displays recycling guidance.
7. Ultrasonic sensor checks bin fullness.
8. SG90 servo performs brush sweeping motion if the object is plastic-related.
9. Event data is logged locally and sent to Google Sheets.
10. Google Sheets dashboard shows recognition history and category count pie chart.

---

## 18. Future Improvements

- Replace SG90 with continuous rotation servo or DC motor
- Improve custom YOLO dataset for local recycling categories
- Add multiple physical bins for plastic, can, and paper
- Improve camera enclosure and lighting
- Add Firebase Realtime Database dashboard
- Add mobile notification for full-bin alerts
- Analyze waste trends by day, week, and month

---

## 19. Team Roles

| Member | Role |
|---|---|
| 김유신 | Hardware assembly, code debugging, testing, GitHub, Notion |
| 정문석 | Hardware assembly, Google Sheets dashboard, PPT, Raspberry Pi setup |

---

## 20. Repository

```text
GitHub Repository URL:
https://github.com/VictorKim00/aiot-smart-recycling-system/tree/main
```
