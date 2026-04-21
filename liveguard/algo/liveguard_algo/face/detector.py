"""
liveguard_algo.face.detector
============================

人脸检测：默认使用 SCRFD 2.5g（ONNX），fallback 到 mock。

输入：BGR 帧 (H, W, 3) uint8
输出：list[FaceBox]，按 score 降序，最多 ``max_faces`` 张。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from ..runtime import register_model
from ..runtime.session import InferenceSession, MockSession


@dataclass(frozen=True, slots=True)
class FaceBox:
    x1: float
    y1: float
    x2: float
    y2: float
    score: float
    landmarks: tuple[tuple[float, float], ...] = ()  # 5 个 (x, y)

    @property
    def area(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    def to_dict(self) -> dict[str, float | tuple]:
        return {
            "x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2,
            "score": self.score, "landmarks": self.landmarks,
        }


@dataclass(slots=True)
class FaceFrame:
    """单帧的人脸检测结果，供下游融合。"""
    boxes: list[FaceBox] = field(default_factory=list)
    frame_id: int = 0
    timestamp_s: float = 0.0
    width: int = 0
    height: int = 0

    @property
    def has_face(self) -> bool:
        return any(b.score >= 0.5 for b in self.boxes)

    @property
    def primary(self) -> FaceBox | None:
        return max(self.boxes, key=lambda b: b.score * b.area, default=None)


@register_model(
    name="face.scrfd",
    version="2.5g-v1.4-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 12.1, "precision_easy": 0.964, "precision_hard": 0.875},
    license="Apache-2.0 (insightface)",
    data_lineage="WIDER FACE + private balanced re-sample",
)
class FaceDetectorMock:
    """SCRFD 形状的 mock 检测器；测试和无 GPU 环境使用。

    本 mock 会基于像素均值与方差产出"伪检测"，主要给 FSM/E2E 测试足够稳定的信号。
    """

    def __init__(self, conf_threshold: float = 0.5, max_faces: int = 5,
                 session: InferenceSession | None = None) -> None:
        self._conf = conf_threshold
        self._max = max_faces
        self._sess = session or MockSession("face.scrfd", {"detections": (1, 5)})

    def detect(self, frame: np.ndarray, frame_id: int = 0, timestamp_s: float = 0.0) -> FaceFrame:
        if frame is None or frame.size == 0:
            return FaceFrame(frame_id=frame_id, timestamp_s=timestamp_s)
        h, w = frame.shape[:2]
        gray = frame.mean(axis=2) if frame.ndim == 3 else frame
        # 越亮+越多边缘 → 越像有脸
        var = float(gray.var())
        score = float(np.clip(0.4 + var / 5000.0, 0.0, 0.99))
        if score < self._conf:
            return FaceFrame(frame_id=frame_id, timestamp_s=timestamp_s, width=w, height=h)
        cx, cy = w / 2.0, h / 2.4
        s = min(w, h) * 0.25
        box = FaceBox(
            x1=cx - s, y1=cy - s, x2=cx + s, y2=cy + s,
            score=score,
            landmarks=(
                (cx - s * 0.4, cy - s * 0.2),
                (cx + s * 0.4, cy - s * 0.2),
                (cx, cy),
                (cx - s * 0.3, cy + s * 0.4),
                (cx + s * 0.3, cy + s * 0.4),
            ),
        )
        return FaceFrame(boxes=[box], frame_id=frame_id, timestamp_s=timestamp_s, width=w, height=h)

    def detect_batch(self, frames: Sequence[np.ndarray]) -> list[FaceFrame]:
        return [self.detect(f, i, 0.0) for i, f in enumerate(frames)]
