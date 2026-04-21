"""
liveguard_algo.action.pose
==========================

姿态估计 + 行为活跃度 — 实现 ``REQ-ALG-008``。

策略：
* MoveNet (mock) 输出 17 点 keypoints；只看上半身 7 点（鼻子+双眼+双耳+双肩）。
* 维护一个滑动窗口（默认 4s），计算关键点位移的方差作为"活跃度"。
* 输出 :class:`ActionResult`，包含 ``activity``（0..1）和 ``is_active``。

这有两个用途：
1. 主播在画面内但长期不动（睡着 / 假人）→ 触发额外检查。
2. 反作弊：循环视频会让 keypoints 周期性闪现 → 在 :mod:`fusion.cheat_fsm` 中
   以 ``temporal_coherence_var`` 信号体现。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Sequence

import numpy as np

from ..runtime import register_model

UPPER_BODY_IDX = (0, 1, 2, 3, 4, 5, 6)  # 鼻+双眼+双耳+双肩


@dataclass(frozen=True, slots=True)
class ActionResult:
    activity: float
    upper_body_visible: bool
    keypoints_count: int
    notes: tuple[str, ...] = ()

    @property
    def is_active(self) -> bool:
        return self.activity >= 0.3 and self.upper_body_visible


@register_model(
    name="action.movenet_thunder",
    version="thunder-v4-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 14.5, "coco_kp_oks": 0.717},
    license="Apache-2.0 (TF-Hub)",
    data_lineage="COCO Keypoints",
)
class MoveNetMock:
    def estimate(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or frame.size == 0:
            return np.zeros((17, 3), dtype=np.float32)
        h, w = frame.shape[:2]
        # 上半身 7 点 + 下半身 10 点（mock 用相对像素强度抖动一点）
        rng = np.random.default_rng(int(frame.mean()) if frame.size else 0)
        center = np.array([w / 2.0, h / 2.4])
        offsets = rng.normal(scale=4.0, size=(17, 2))
        anchors = np.array(
            [
                [0, -90], [-15, -100], [15, -100], [-30, -95], [30, -95],
                [-45, -50], [45, -50], [-50, 0], [50, 0], [-30, 60], [30, 60],
                [-25, 70], [25, 70], [-20, 130], [20, 130], [-15, 200], [15, 200],
            ]
        )
        kps = np.concatenate(
            [center + anchors + offsets, np.full((17, 1), 0.85, dtype=np.float32)],
            axis=1,
        ).astype(np.float32)
        return kps


class ActionScorerMock:
    """对一段时间内的关键点轨迹做活跃度评分。"""

    def __init__(self, window: int = 100, kp_threshold: float = 0.3) -> None:
        self._buf: Deque[np.ndarray] = deque(maxlen=window)
        self._kp_th = kp_threshold

    def feed(self, keypoints: np.ndarray) -> ActionResult:
        if keypoints.shape != (17, 3):
            return ActionResult(0.0, False, 0, ("bad_shape",))
        upper = keypoints[list(UPPER_BODY_IDX)]
        upper_visible = bool(np.mean(upper[:, 2] >= self._kp_th) > 0.5)
        self._buf.append(upper[:, :2].copy())

        if len(self._buf) < 5:
            return ActionResult(0.0, upper_visible, len(self._buf), ("warming",))

        arr = np.stack(list(self._buf), axis=0)  # (T, 7, 2)
        # 时间维方差再对 7 点求平均
        var_per_kp = arr.var(axis=0).mean(axis=1)  # (7,)
        activity = float(np.clip(var_per_kp.mean() / 25.0, 0.0, 1.0))

        notes: list[str] = []
        if not upper_visible:
            notes.append("upper_body_missing")
        if activity < 0.05:
            notes.append("very_static_subject")

        return ActionResult(activity, upper_visible, 7, tuple(notes))

    def reset(self) -> None:
        self._buf.clear()

    def feed_batch(self, kps: Sequence[np.ndarray]) -> list[ActionResult]:
        return [self.feed(k) for k in kps]
