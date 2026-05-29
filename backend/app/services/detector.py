"""
PPEDetector — dual-backend YOLO inference wrapper.

Supported weight formats
────────────────────────
  best.onnx   → inference via onnxruntime  (no PyTorch, fast, recommended)
  best.pt     → inference via PyTorch + Ultralytics  (requires torch install)

detect_frame()  → single-frame inference, no tracking state
track_frame()   → inference + ByteTrack  (only available with .pt + torch)
                  Falls back to detect_frame() when using ONNX backend.

Both return a list of detection dicts:
    {
        "class_name": str,
        "confidence": float,      # 0.0–1.0
        "bbox_xyxy":  [x1, y1, x2, y2],
        "track_id":   int | None,
    }

ONNX export (run once, needs torch on the training machine):
    from ultralytics import YOLO
    YOLO("best.pt").export(format="onnx", imgsz=640, simplify=True)
    # → produces best.onnx
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Class name normalizer ──────────────────────────────────────────────────────
# Maps raw dataset class names (lower-cased) → canonical names the ViolationEngine
# frozensets recognise.  Needed because the Roboflow Construction Site Safety
# dataset uses hyphens ("NO-Hardhat") while our engine uses underscores.
_NORMALIZE_CLASS: dict[str, str] = {
    # Roboflow hyphenated → underscore canonical
    "no-hardhat":      "no_hardhat",
    "no-helmet":       "no_helmet",
    "no-safety vest":  "no_vest",
    "no-safety-vest":  "no_vest",
    "no-vest":         "no_vest",
    # spaced → underscore
    "safety vest":     "safety_vest",
    "safety-vest":     "safety_vest",
    "hard hat":        "hardhat",
    "hard_hat":        "hardhat",
    # human-readable → canonical
    "worker":          "person",
}


def normalize_class(raw: str) -> str:
    """Return the canonical class name for a raw YOLO detection class."""
    lower = raw.lower()
    return _NORMALIZE_CLASS.get(lower, lower)


# ── BGR annotation colours ────────────────────────────────────────────────────
CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    # persons
    "person":           (30,  144, 255),
    # helmets / hard hats
    "helmet":           (0,   200,   0),
    "hardhat":          (0,   200,   0),
    # violations
    "no_helmet":        (0,     0, 220),
    "no_hardhat":       (0,     0, 220),
    # vests
    "vest":             (0,   200,   0),
    "safety_vest":      (0,   200,   0),
    # vest violations
    "no_vest":          (0,     0, 220),
    "no_safety_vest":   (0,     0, 220),
    # other
    "mask":             (0,   180, 180),
    "no_mask":          (0,     0, 220),
    "safety_cone":      (255, 165,   0),
    "machinery":        (180,   0, 220),
    "vehicle":          (180,   0, 220),
}
_DEFAULT_COLOR: tuple[int, int, int] = (160, 160, 160)


def color_for(class_name: str) -> tuple[int, int, int]:
    return CLASS_COLORS.get(normalize_class(class_name), _DEFAULT_COLOR)


# ── detector ──────────────────────────────────────────────────────────────────

class PPEDetector:
    """
    Wraps either an ONNX or a PyTorch YOLO model for PPE detection.

    Reuse the same instance across all frames of one video — the ByteTrack
    state (when using .pt + torch) lives inside the model object.
    """

    def __init__(
        self,
        weights_path: str,
        confidence: float = 0.4,
        iou_threshold: float = 0.45,
        device: str = "cpu",
    ) -> None:
        self.weights_path = Path(weights_path)
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.device = device
        self._backend: str = ""       # "onnx" | "torch"
        self._model: Any = None
        self._class_names: dict[int, str] = {}

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def load(self) -> None:
        if not self.weights_path.exists():
            raise FileNotFoundError(
                f"Model weights not found: {self.weights_path}\n"
                "Options:\n"
                "  • Place best.onnx at backend/weights/best.pt  (recommended)\n"
                "  • Or export from PyTorch: YOLO('best.pt').export(format='onnx')\n"
                "  • Or train from scratch: python training/train_yolo.py"
            )

        suffix = self.weights_path.suffix.lower()

        if suffix == ".onnx":
            self._load_onnx()
        elif suffix == ".pt":
            self._load_torch()
        else:
            raise ValueError(
                f"Unsupported weight format: {suffix}. Use .onnx or .pt"
            )

    def _load_onnx(self) -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ImportError(
                "onnxruntime is not installed.\n"
                "Run: pip install onnxruntime"
            ) from exc

        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if self.device != "cpu"
            else ["CPUExecutionProvider"]
        )
        self._model = ort.InferenceSession(
            str(self.weights_path), providers=providers
        )
        # Try to read class names from model metadata
        try:
            meta = self._model.get_modelmeta().custom_metadata_map
            import json
            self._class_names = {
                int(k): v for k, v in json.loads(meta.get("names", "{}")).items()
            }
        except Exception:
            self._class_names = {}

        self._backend = "onnx"
        logger.info(
            "ONNX model loaded  path=%s  classes=%s",
            self.weights_path,
            list(self._class_names.values()) or "unknown (no metadata)",
        )

    def _load_torch(self) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError(
                "ultralytics is not installed.\n"
                "Run: pip install ultralytics"
            ) from exc
        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "PyTorch is not installed.\n"
                "For .pt inference: pip install torch\n"
                "Or convert your model: YOLO('best.pt').export(format='onnx')\n"
                "Then place best.onnx at backend/weights/best.onnx"
            ) from exc

        self._model = YOLO(str(self.weights_path))
        self._class_names = dict(self._model.names)
        self._backend = "torch"
        logger.info(
            "PyTorch model loaded  path=%s  classes=%s",
            self.weights_path,
            list(self._class_names.values()),
        )

    def _ensure_loaded(self) -> None:
        if self._model is None:
            self.load()

    # ── inference API ─────────────────────────────────────────────────────────

    def detect_frame(self, frame: Any) -> list[dict]:
        """Single-frame inference, no persistent tracking state."""
        self._ensure_loaded()
        if self._backend == "onnx":
            return self._infer_onnx(frame)
        return self._infer_torch(frame, track=False)

    def track_frame(self, frame: Any) -> list[dict]:
        """
        Inference + ByteTrack.
        For ONNX models: falls back to detect_frame() (no track IDs).
        For .pt models:  full ByteTrack support; call in frame order.
        """
        self._ensure_loaded()
        if self._backend == "onnx":
            logger.debug("ONNX backend: tracking not available, using detect_frame()")
            return self._infer_onnx(frame)
        return self._infer_torch(frame, track=True)

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def class_names(self) -> dict[int, str]:
        self._ensure_loaded()
        return self._class_names

    @property
    def backend(self) -> str:
        return self._backend

    # ── ONNX inference ────────────────────────────────────────────────────────

    def _infer_onnx(self, frame: Any) -> list[dict]:
        import numpy as np
        import cv2

        h, w = frame.shape[:2]
        input_size = 640

        # Letterbox resize
        scale = min(input_size / w, input_size / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (nw, nh))
        padded = np.full((input_size, input_size, 3), 114, dtype=np.uint8)
        pad_x = (input_size - nw) // 2
        pad_y = (input_size - nh) // 2
        padded[pad_y:pad_y + nh, pad_x:pad_x + nw] = resized

        # BGR → RGB, HWC → NCHW, normalise
        blob = (
            padded[:, :, ::-1]
            .transpose(2, 0, 1)
            .astype(np.float32)[np.newaxis]
            / 255.0
        )

        input_name = self._model.get_inputs()[0].name
        raw = self._model.run(None, {input_name: blob})[0]  # shape (1, num_det, 6+)

        detections: list[dict] = []
        # YOLOv8 ONNX output: [batch, num_classes+4, num_anchors] → needs transpose
        # Handle both old (anchors, 5+classes) and new (4+classes, anchors) layouts
        preds = raw[0]
        if preds.shape[0] < preds.shape[1]:
            preds = preds.T   # new YOLOv8 layout

        for row in preds:
            # row: [x_c, y_c, w, h, cls0_conf, cls1_conf, ...]
            xc, yc, bw, bh = row[:4]
            class_scores = row[4:]
            cls_id = int(np.argmax(class_scores))
            conf = float(class_scores[cls_id])
            if conf < self.confidence:
                continue

            # De-letterbox: back to original frame coordinates
            x1 = int(((xc - bw / 2) - pad_x) / scale)
            y1 = int(((yc - bh / 2) - pad_y) / scale)
            x2 = int(((xc + bw / 2) - pad_x) / scale)
            y2 = int(((yc + bh / 2) - pad_y) / scale)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            raw_name = self._class_names.get(cls_id, str(cls_id))
            detections.append(
                {
                    "class_name": normalize_class(raw_name),
                    "confidence": round(conf, 4),
                    "bbox_xyxy":  [x1, y1, x2, y2],
                    "track_id":   None,
                }
            )
        return detections

    # ── PyTorch / Ultralytics inference ───────────────────────────────────────

    def _infer_torch(self, frame: Any, track: bool) -> list[dict]:
        if track:
            # Use custom tracker config for stable construction-site tracking
            _tracker_cfg = str(self.weights_path.parent / "bytetrack.yaml")
            if not Path(_tracker_cfg).exists():
                _tracker_cfg = "bytetrack.yaml"
            results = self._model.track(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                persist=True,
                tracker=_tracker_cfg,
                verbose=False,
                device=self.device,
            )
        else:
            results = self._model(
                frame,
                conf=self.confidence,
                iou=self.iou_threshold,
                verbose=False,
                device=self.device,
            )

        result = results[0]
        ids: Optional[list[int]] = None
        if track and result.boxes.id is not None:
            ids = result.boxes.id.int().cpu().tolist()

        names: dict = result.names
        detections: list[dict] = []
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls[0])
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            tid: Optional[int] = (
                int(ids[i])
                if ids is not None and i < len(ids) and ids[i] is not None
                else None
            )
            raw_name = names.get(cls_id, str(cls_id))
            detections.append(
                {
                    "class_name": normalize_class(raw_name),
                    "confidence": round(float(box.conf[0]), 4),
                    "bbox_xyxy":  [x1, y1, x2, y2],
                    "track_id":   tid,
                }
            )
        return detections
