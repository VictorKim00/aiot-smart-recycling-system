"""Validate trained custom YOLO model on laptop before moving best.pt to Raspberry Pi."""
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default="runs/waste/waste_custom/weights/best.pt")
    parser.add_argument("--data", default="datasets/waste/data.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz, device=args.device)
    print(metrics)


if __name__ == "__main__":
    main()
