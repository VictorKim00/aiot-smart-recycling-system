"""Train a custom YOLO detector on a laptop/Colab, then copy best.pt to Raspberry Pi.

This script is for the laptop, not for Raspberry Pi deployment.
Example:
    python scripts/train_custom_yolo.py --data datasets/waste/data.yaml --model yolov8n.pt --epochs 80 --imgsz 640 --batch 16 --device 0
"""
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="datasets/waste/data.yaml", help="Path to data.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model, e.g. yolov8n.pt or yolov8s.pt")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="0", help="0 for GPU, cpu for CPU")
    parser.add_argument("--project", default="runs/waste")
    parser.add_argument("--name", default="waste_custom")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise FileNotFoundError(f"data.yaml not found: {data_path}")

    model = YOLO(args.model)
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        pretrained=True,
        patience=20,
        plots=True,
    )
    print(results)
    print("Training complete.")
    print(f"Copy this file to Raspberry Pi project/models/best.pt:")
    print(Path(args.project) / args.name / "weights" / "best.pt")


if __name__ == "__main__":
    main()
