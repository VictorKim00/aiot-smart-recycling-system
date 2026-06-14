# Custom YOLO 학습 가이드: laptop/Colab에서 학습 후 best.pt만 Raspberry Pi로 이동

## 목표 class

최소 3개 class로 학습합니다.

```text
0: plastic_bottle
1: can
2: paper
```

최종 Pi 코드의 `modules/waste_rules.py`가 이 label을 각각 `plastic`, `can`, `paper`로 매핑합니다.

## 데이터 수집 권장량

최소 데모용:

- plastic_bottle: 100장 이상
- can: 100장 이상
- paper: 100장 이상

가능하면 더 좋음:

- class당 300장 이상
- 다양한 배경, 조명, 각도, 거리
- 실제 데모 장소와 비슷한 배경 포함
- 찌그러진 캔, 투명 페트병, 구겨진 종이도 포함

## 폴더 구조

```text
smart_recycling_training/
├── datasets/
│   └── waste/
│       ├── images/
│       │   ├── train/
│       │   └── val/
│       ├── labels/
│       │   ├── train/
│       │   └── val/
│       └── data.yaml
└── scripts/
    ├── train_custom_yolo.py
    ├── validate_custom_yolo.py
    └── predict_folder.py
```

이미지와 label txt 파일 이름은 반드시 같아야 합니다.

```text
images/train/bottle_001.jpg
labels/train/bottle_001.txt
```

## YOLO label 형식

각 `.txt` 파일은 object 1개당 한 줄입니다.

```text
class_id x_center y_center width height
```

좌표는 모두 0~1로 정규화된 값입니다.

예시:

```text
0 0.512 0.488 0.240 0.610
```

## data.yaml

```yaml
path: datasets/waste
train: images/train
val: images/val

names:
  0: plastic_bottle
  1: can
  2: paper
```

## 학습 실행

GPU 노트북 또는 Colab 기준:

```bash
python scripts/train_custom_yolo.py --data datasets/waste/data.yaml --model yolov8n.pt --epochs 80 --imgsz 640 --batch 16 --device 0
```

GPU 메모리가 부족하면:

```bash
python scripts/train_custom_yolo.py --data datasets/waste/data.yaml --model yolov8n.pt --epochs 80 --imgsz 640 --batch 8 --device 0
```

CPU만 있으면 오래 걸리지만 가능은 합니다.

```bash
python scripts/train_custom_yolo.py --data datasets/waste/data.yaml --model yolov8n.pt --epochs 50 --imgsz 640 --batch 4 --device cpu
```

## 결과 확인

학습 결과는 보통 아래에 생성됩니다.

```text
runs/waste/waste_custom/weights/best.pt
runs/waste/waste_custom/results.png
runs/waste/waste_custom/confusion_matrix.png
```

검증:

```bash
python scripts/validate_custom_yolo.py --weights runs/waste/waste_custom/weights/best.pt --data datasets/waste/data.yaml --device 0
```

예측 이미지 저장:

```bash
python scripts/predict_folder.py --weights runs/waste/waste_custom/weights/best.pt --source datasets/waste/images/val
```

## Raspberry Pi로 옮기기

노트북에서 나온 파일:

```text
runs/waste/waste_custom/weights/best.pt
```

이 파일만 Raspberry Pi 프로젝트의 아래 위치로 복사합니다.

```text
aiot_recycling_ultrasonic_fullness_code/models/best.pt
```

그 다음 Pi에서:

```bash
python tests/test_camera_yolo.py
python main.py
```

## 성능이 낮을 때 개선 순서

1. 데모 장소와 같은 배경에서 사진을 더 찍습니다.
2. 투명 페트병, 찌그러진 캔, 구겨진 종이처럼 어려운 예시를 추가합니다.
3. train/val 분리가 잘 되었는지 확인합니다. 같은 장면이 train과 val에 중복되면 실제 성능보다 높게 보입니다.
4. `epochs`를 80에서 120으로 늘립니다.
5. `yolov8n.pt`에서 `yolov8s.pt`로 올립니다. 단, Raspberry Pi inference 속도는 느려질 수 있습니다.
6. confidence threshold를 Pi `config.py`에서 조절합니다.

```python
DETECTION_CONF_THRESHOLD = 0.45
```

오인식이 많으면 0.55 정도로 올리고, 인식이 너무 안 되면 0.35~0.40으로 낮춥니다.
