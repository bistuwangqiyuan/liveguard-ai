"""
liveguard_algo.fusion.cheat_fsm
===============================

反作弊子状态机 — 与主在岗状态机并行运行。

实现 ``Requirements REQ-SYS-004 / REQ-ALGO-008``、``Design §6.4``。

5 类作弊检测：

* ``STATIC_PHOTO``       —— 静态照片回放（活体得分长时间偏低）
* ``LOOPED_VIDEO``       —— 循环视频（音频静默 + 时序自相关高）
* ``DEEPFAKE_AVATAR``    —— AI 数字人（deepfake 检测器命中）
* ``IMPERSONATION``      —— 替身代播（Re-ID 与登记主播差异显著）
* ``SCREEN_REPLAY``      —— 屏幕翻拍（场景特征统计异常 — 由上层提供 ``screen_score``）

输出：每次 :meth:`CheatFSM.feed` 返回 0 或多个 :class:`CheatFlag`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CheatPattern(str, Enum):
    STATIC_PHOTO = "STATIC_PHOTO"
    LOOPED_VIDEO = "LOOPED_VIDEO"
    DEEPFAKE_AVATAR = "DEEPFAKE_AVATAR"
    IMPERSONATION = "IMPERSONATION"
    SCREEN_REPLAY = "SCREEN_REPLAY"


@dataclass(frozen=True, slots=True)
class CheatSignals:
    """作弊检测所需的额外信号。

    所有信号 ∈ [0, 1]。"""

    liveness_score: float = 1.0
    """活体得分；越低越像静态画面/数字人。"""
    deepfake_score: float = 0.0
    """deepfake 概率；越高越可能是数字人。"""
    reid_similarity: float = 1.0
    """与登记主播 Re-ID 余弦相似度。"""
    audio_active: float = 1.0
    """音频活动度（VAD）。"""
    temporal_coherence_var: float = 0.5
    """时序帧差方差；过低表示循环画面。"""
    screen_replay_score: float = 0.0
    """屏幕翻拍特征得分。"""


@dataclass(slots=True)
class CheatFlag:
    pattern: CheatPattern
    confidence: float
    evidence: dict[str, float] = field(default_factory=dict)
    severity: str = "P1"


@dataclass(frozen=True, slots=True)
class CheatThresholds:
    photo_liveness_max: float = 0.50
    photo_window_s: float = 5.0
    deepfake_min: float = 0.70
    impersonation_max: float = 0.55
    impersonation_window_s: float = 10.0
    looped_var_max: float = 0.02
    looped_audio_inactive_max: float = 0.10
    looped_window_s: float = 10.0
    screen_replay_min: float = 0.75


DEFAULT_CHEAT_THRESHOLDS = CheatThresholds()


class CheatFSM:
    """简单的累积窗口检测器集合（每个 pattern 独立计时）。"""

    __slots__ = (
        "stream_id",
        "thresholds",
        "_timers",
        "_active",
    )

    def __init__(self, stream_id: str = "default", thresholds: CheatThresholds = DEFAULT_CHEAT_THRESHOLDS) -> None:
        self.stream_id = stream_id
        self.thresholds = thresholds
        self._timers: dict[CheatPattern, float] = {p: 0.0 for p in CheatPattern}
        self._active: set[CheatPattern] = set()

    @property
    def active_flags(self) -> set[CheatPattern]:
        return set(self._active)

    def reset(self, pattern: Optional[CheatPattern] = None) -> None:
        if pattern is None:
            for p in CheatPattern:
                self._timers[p] = 0.0
            self._active.clear()
        else:
            self._timers[pattern] = 0.0
            self._active.discard(pattern)

    def feed(self, signals: CheatSignals, dt: float) -> list[CheatFlag]:
        if dt <= 0:
            raise ValueError("dt 必须 > 0")
        flags: list[CheatFlag] = []
        th = self.thresholds

        flags.extend(self._check_photo(signals, dt, th))
        flags.extend(self._check_deepfake(signals, th))
        flags.extend(self._check_impersonation(signals, dt, th))
        flags.extend(self._check_looped(signals, dt, th))
        flags.extend(self._check_screen_replay(signals, th))

        return flags

    # ------------------------------------------------------------------ private

    def _check_photo(self, s: CheatSignals, dt: float, th: CheatThresholds) -> list[CheatFlag]:
        if s.liveness_score < th.photo_liveness_max:
            self._timers[CheatPattern.STATIC_PHOTO] += dt
            if (
                self._timers[CheatPattern.STATIC_PHOTO] >= th.photo_window_s
                and CheatPattern.STATIC_PHOTO not in self._active
            ):
                self._active.add(CheatPattern.STATIC_PHOTO)
                return [
                    CheatFlag(
                        pattern=CheatPattern.STATIC_PHOTO,
                        confidence=round(1.0 - s.liveness_score, 3),
                        evidence={"liveness_score": s.liveness_score, "timer_s": self._timers[CheatPattern.STATIC_PHOTO]},
                        severity="P0",
                    )
                ]
        else:
            self._timers[CheatPattern.STATIC_PHOTO] = 0.0
            self._active.discard(CheatPattern.STATIC_PHOTO)
        return []

    def _check_deepfake(self, s: CheatSignals, th: CheatThresholds) -> list[CheatFlag]:
        if s.deepfake_score >= th.deepfake_min and CheatPattern.DEEPFAKE_AVATAR not in self._active:
            self._active.add(CheatPattern.DEEPFAKE_AVATAR)
            return [
                CheatFlag(
                    pattern=CheatPattern.DEEPFAKE_AVATAR,
                    confidence=round(s.deepfake_score, 3),
                    evidence={"deepfake_score": s.deepfake_score},
                    severity="P0",
                )
            ]
        if s.deepfake_score < th.deepfake_min * 0.8:
            self._active.discard(CheatPattern.DEEPFAKE_AVATAR)
        return []

    def _check_impersonation(self, s: CheatSignals, dt: float, th: CheatThresholds) -> list[CheatFlag]:
        if s.reid_similarity < th.impersonation_max:
            self._timers[CheatPattern.IMPERSONATION] += dt
            if (
                self._timers[CheatPattern.IMPERSONATION] >= th.impersonation_window_s
                and CheatPattern.IMPERSONATION not in self._active
            ):
                self._active.add(CheatPattern.IMPERSONATION)
                return [
                    CheatFlag(
                        pattern=CheatPattern.IMPERSONATION,
                        confidence=round(1.0 - s.reid_similarity, 3),
                        evidence={
                            "reid_similarity": s.reid_similarity,
                            "timer_s": self._timers[CheatPattern.IMPERSONATION],
                        },
                        severity="P0",
                    )
                ]
        else:
            self._timers[CheatPattern.IMPERSONATION] = 0.0
            self._active.discard(CheatPattern.IMPERSONATION)
        return []

    def _check_looped(self, s: CheatSignals, dt: float, th: CheatThresholds) -> list[CheatFlag]:
        if (
            s.temporal_coherence_var < th.looped_var_max
            and s.audio_active < th.looped_audio_inactive_max
        ):
            self._timers[CheatPattern.LOOPED_VIDEO] += dt
            if (
                self._timers[CheatPattern.LOOPED_VIDEO] >= th.looped_window_s
                and CheatPattern.LOOPED_VIDEO not in self._active
            ):
                self._active.add(CheatPattern.LOOPED_VIDEO)
                return [
                    CheatFlag(
                        pattern=CheatPattern.LOOPED_VIDEO,
                        confidence=0.85,
                        evidence={
                            "temporal_var": s.temporal_coherence_var,
                            "audio_active": s.audio_active,
                            "timer_s": self._timers[CheatPattern.LOOPED_VIDEO],
                        },
                        severity="P1",
                    )
                ]
        else:
            self._timers[CheatPattern.LOOPED_VIDEO] = 0.0
            self._active.discard(CheatPattern.LOOPED_VIDEO)
        return []

    def _check_screen_replay(self, s: CheatSignals, th: CheatThresholds) -> list[CheatFlag]:
        if s.screen_replay_score >= th.screen_replay_min and CheatPattern.SCREEN_REPLAY not in self._active:
            self._active.add(CheatPattern.SCREEN_REPLAY)
            return [
                CheatFlag(
                    pattern=CheatPattern.SCREEN_REPLAY,
                    confidence=round(s.screen_replay_score, 3),
                    evidence={"screen_replay_score": s.screen_replay_score},
                    severity="P1",
                )
            ]
        if s.screen_replay_score < th.screen_replay_min * 0.8:
            self._active.discard(CheatPattern.SCREEN_REPLAY)
        return []
