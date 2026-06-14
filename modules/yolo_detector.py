from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import cv2
import numpy as np
import onnxruntime as ort

import config
from modules.waste_rules import label_to_category


@dataclass
class DetectionResult:
    status: str = "no_detection"  # ok, uncertain, no_detection
    label: str = ""
    category: str = "unknown"
    confidence: float = 0.0
    box: tuple[int, int, int, int] | None = None


class YOLODetector:
    """YOLOv8 ONNX detector for Raspberry Pi.

    This final project version avoids ultralytics/torch on Raspberry Pi.
    Export best.pt to best.onnx in Colab, then copy it to models/best.onnx.
    Expected output for 3 classes is usually (1, 7, 8400):
        x_center, y_center, width, height, class0, class1, class2
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = str(model_path or config.MODEL_PATH)
        self.names = ["plastic_bottle", "can", "paper"]
        self.imgsz = int(config.YOLO_IMAGE_SIZE)
        self.ok_conf_thres = float(config.DETECTION_CONF_THRESHOLD)
        self.pred_conf_thres = float(config.UNCERTAIN_CONF_THRESHOLD)
        self.iou_thres = 0.45

        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"ONNX model not found: {self.model_path}\n"
                "Copy your Colab-exported model to models/best.onnx."
            )

        self.session = ort.InferenceSession(
            self.model_path,
            providers=["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name
        print(f"[YOLO] Using ONNX Runtime: {self.model_path}")

    def _letterbox(self, img: np.ndarray) -> tuple[np.ndarray, float, tuple[float, float]]:
        h0, w0 = img.shape[:2]
        r = min(self.imgsz / h0, self.imgsz / w0)
        new_w, new_h = int(round(w0 * r)), int(round(h0 * r))
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        canvas = np.full((self.imgsz, self.imgsz, 3), 114, dtype=np.uint8)
        dw = (self.imgsz - new_w) / 2
        dh = (self.imgsz - new_h) / 2
        left, top = int(round(dw - 0.1)), int(round(dh - 0.1))
        canvas[top: top + new_h, left: left + new_w] = resized
        return canvas, r, (left, top)

    def _preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, float, tuple[float, float], int, int]:
        h0, w0 = frame.shape[:2]
        img, ratio, pad = self._letterbox(frame)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        x = img.astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))
        x = np.expand_dims(x, axis=0)
        return x, ratio, pad, w0, h0

    def _scale_box(self, cx: float, cy: float, w: float, h: float, ratio: float, pad: tuple[float, float], w0: int, h0: int):
        px, py = pad
        x1 = (cx - w / 2 - px) / ratio
        y1 = (cy - h / 2 - py) / ratio
        x2 = (cx + w / 2 - px) / ratio
        y2 = (cy + h / 2 - py) / ratio
        x1 = int(max(0, min(w0 - 1, x1)))
        y1 = int(max(0, min(h0 - 1, y1)))
        x2 = int(max(0, min(w0 - 1, x2)))
        y2 = int(max(0, min(h0 - 1, y2)))
        return x1, y1, x2, y2

    def _postprocess(self, outputs, ratio: float, pad: tuple[float, float], w0: int, h0: int) -> list[dict]:
        pred = np.squeeze(outputs[0])
        if pred.ndim != 2:
            return []

        # YOLOv8 ONNX is usually (7, 8400), convert to (8400, 7).
        if pred.shape[0] < pred.shape[1]:
            pred = pred.T

        boxes_xywh = []
        scores = []
        class_ids = []
        boxes_xyxy = []

        for row in pred:
            if len(row) < 4 + len(self.names):
                continue

            cx, cy, w, h = row[:4]
            class_scores = row[4:4 + len(self.names)]
            class_id = int(np.argmax(class_scores))
            score = float(class_scores[class_id])

            if score < self.pred_conf_thres:
                continue

            x1, y1, x2, y2 = self._scale_box(float(cx), float(cy), float(w), float(h), ratio, pad, w0, h0)
            bw, bh = max(0, x2 - x1), max(0, y2 - y1)
            if bw <= 1 or bh <= 1:
                continue

            boxes_xywh.append([x1, y1, bw, bh])
            boxes_xyxy.append((x1, y1, x2, y2))
            scores.append(score)
            class_ids.append(class_id)

        if not boxes_xywh:
            return []

        indices = cv2.dnn.NMSBoxes(boxes_xywh, scores, self.pred_conf_thres, self.iou_thres)
        results = []
        if len(indices) > 0:
            for i in np.array(indices).flatten():
                cls_id = class_ids[i]
                label = self.names[cls_id]
                results.append({
                    "label": label,
                    "category": label_to_category(label),
                    "confidence": float(scores[i]),
                    "box": boxes_xyxy[i],
                })

        # Prefer known recycling categories, then confidence.
        results.sort(key=lambda r: (r["category"] != "unknown", r["confidence"]), reverse=True)
        return results

    def detect_with_annotated(self, frame) -> tuple[DetectionResult, object]:
        start = time.time()
        x, ratio, pad, w0, h0 = self._preprocess(frame)
        outputs = self.session.run(None, {self.input_name: x})
        detections = self._postprocess(outputs, ratio, pad, w0, h0)

        annotated = frame.copy()
        if not detections:
            return DetectionResult(status="no_detection"), annotated

        best = detections[0]
        label = best["label"]
        category = best["category"]
        conf = float(best["confidence"])
        box = best["box"]

        x1, y1, x2, y2 = box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            f"{label} {conf:.2f}",
            (x1, max(22, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            annotated,
            f"{(time.time() - start) * 1000:.0f} ms",
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        if conf >= self.ok_conf_thres and category != "unknown":
            status = "ok"
        elif conf >= self.pred_conf_thres:
            status = "uncertain"
        else:
            status = "no_detection"

        return DetectionResult(
            status=status,
            label=label,
            category=category,
            confidence=conf,
            box=box,
        ), annotated

    def detect(self, frame) -> DetectionResult:
        detection, _ = self.detect_with_annotated(frame)
        return detection
