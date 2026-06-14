"""Run prediction on test photos to visually inspect custom model performance."""
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default="runs/waste/waste_custom/weights/best.pt")
    parser.add_argument("--source", default="datasets/waste/images/val")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    model = YOLO(args.weights)
    model.predict(source=args.source, conf=args.conf, imgsz=args.imgsz, save=True, save_txt=True)


if __name__ == "__main__":
    main()
