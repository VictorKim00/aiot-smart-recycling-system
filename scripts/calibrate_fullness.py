"""Calibrate HC-SR04 fullness distances.

Run from project root:
    python scripts/calibrate_fullness.py --mode empty
    python scripts/calibrate_fullness.py --mode full
    python scripts/calibrate_fullness.py --mode set-full --full-cm 6
"""
from __future__ import annotations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import argparse
from modules.fullness_monitor import FullnessMonitor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["empty", "full", "set-full", "show"], default="show")
    parser.add_argument("--full-cm", type=float, default=None)
    parser.add_argument("--samples", type=int, default=10)
    args = parser.parse_args()

    monitor = FullnessMonitor()
    try:
        if args.mode == "empty":
            print("Make sure the bin is empty. Measuring empty distance...")
            print(monitor.calibrate_empty(samples=args.samples))
        elif args.mode == "full":
            print("Place material at the height considered FULL. Measuring full distance...")
            print(monitor.calibrate_full(samples=args.samples))
        elif args.mode == "set-full":
            if args.full_cm is None:
                raise SystemExit("--full-cm is required for --mode set-full")
            print(monitor.calibrate_full(full_distance_cm=args.full_cm, samples=args.samples))
        else:
            print("Current calibration:")
            print(monitor.calibration)
            print("Current readings:")
            print(monitor.read_all())
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
