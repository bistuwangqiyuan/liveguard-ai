"""
liveguard_algo.person.detector
==============================

人形检测：YOLOv8n-pose-tiny / RT-DETR-tiny；mock 返回稳定的伪检测。

设计：与 :mod:`face.detector` 保持一致的 API（``detect`` / ``detect_batch``），
方便 multi-modal pipeline 统一调度。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..runtime import register_model


@dataclass(frozen=True, slots=True)
class PersonBox:
    x1: float
    y1: float
    x2: float
    y2: float
    score: float
    keypoints: tuple[tuple[float, float, float], ...] = ()  # (x, y, conf) × 17

    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)


@dataclass(slots=True)
class PersonFrame:
    boxes: list[PersonBox] = field(default_factory=list)
    frame_id: int = 0
    timestamp_s: float = 0.0
    width: int = 0
    height: int = 0

    @property
    def has_person(self) -> bool:
        return any(b.score >= 0.4 for b in self.boxes)

    @property
    def primary(self) -> PersonBox | None:
        return max(self.boxes, key=lambda b: b.score * b.area, default=None)


@register_model(
    name="person.yolov8n",
    version="yolov8n-pose-v8.2-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 18.0, "coco_map": 0.504, "coco_map50": 0.683},
    license="AGPL-3.0 (Ultralytics) — commercial license required",
    data_lineage="COCO + private retail livestream subset",
)
class PersonDetectorMock:
    def __init__(self, conf_threshold: float = 0.4, max_persons: int = 3) -> None:
        self._conf = conf_threshold
        self._max = max_persons

    def detect(self, frame: np.ndarray, frame_id: int = 0, timestamp_s: float = 0.0) -> PersonFrame:
        if frame is None or frame.size == 0:
            return PersonFrame(frame_id=frame_id, timestamp_s=timestamp_s)
        h, w = frame.shape[:2]
        gray = frame.mean(axis=2) if frame.ndim == 3 else frame
        var = float(gray.var())
        score = float(np.clip(0.35 + var / 5500.0, 0.0, 0.97))
        if score < self._conf:
            return PersonFrame(frame_id=frame_id, timestamp_s=timestamp_s, width=w, height=h)
        cx = w / 2.0
        return PersonFrame(
            boxes=[PersonBox(x1=cx - w * 0.18, y1=h * 0.05, x2=cx + w * 0.18, y2=h * 0.95, score=score)],
            frame_id=frame_id, timestamp_s=timestamp_s, width=w, height=h,
        )
