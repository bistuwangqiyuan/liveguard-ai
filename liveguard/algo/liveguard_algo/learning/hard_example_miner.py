"""
liveguard_algo.learning.hard_example_miner
==========================================

持续学习 / 难例挖掘 (Hard Example Mining) — 实现 ``REQ-ALGO-014`` /
``Design §5.6 Continuous Learning``。

策略
----

1. **不确定性挖掘 (Uncertainty Sampling)**：``|score - 0.5|`` 接近 0 的样本
   是模型最"为难"的，挖掘它们做主动学习。
2. **不一致挖掘 (Disagreement Sampling)**：当 6 路信号方差大、但结论是"在岗/离岗"
   时，往往是 spoofing 或边缘案例。
3. **失败挖掘 (Failure Mining)**：状态升级到 P0 后人工标注为 false alarm 时，
   样本权重提高，纳入下一个 fine-tuning 数据集。

输出 :class:`HardExample` 写入 :mod:`liveguard_algo.learning.dataset_writer`
（落 S3 + 元数据入 Postgres）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np

from ..fusion.state_machine import SignalFrame, StateTransitionEvent, StreamState


@dataclass(frozen=True, slots=True)
class MinerConfig:
    uncertainty_band: float = 0.10
    """``|score-0.5| < band`` 的样本被认为是"不确定"。"""
    disagreement_var_min: float = 0.06
    """6 路信号方差超过该值视为不一致。"""
    sample_rate: float = 1.0
    """全局采样率，1.0 表示全采，0.1 表示 10% 采样。"""
    keep_max_per_minute: int = 30
    """节流：每分钟最多挖掘多少条，避免存储爆炸。"""


@dataclass(slots=True)
class HardExample:
    sample_id: str
    stream_id: str
    timestamp_s: float
    fusion_score: float
    signals: SignalFrame
    reason: str  # "uncertainty" | "disagreement" | "user_feedback"
    labels: dict[str, str] = field(default_factory=dict)
    weight: float = 1.0
    artifact_uri: str = ""

    def to_audit(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "stream_id": self.stream_id,
            "ts_s": self.timestamp_s,
            "fusion": round(self.fusion_score, 4),
            "reason": self.reason,
            "weight": self.weight,
            "labels": self.labels,
        }


class HardExampleMiner:
    """流式难例挖掘器；线程不安全（每流一份）。"""

    __slots__ = ("config", "_window_index", "_count_in_window", "_kept")

    def __init__(self, config: MinerConfig | None = None) -> None:
        self.config = config or MinerConfig()
        self._window_index: int = -1
        self._count_in_window: int = 0
        self._kept: list[HardExample] = []

    @property
    def collected(self) -> list[HardExample]:
        return list(self._kept)

    def consider(
        self,
        *,
        stream_id: str,
        signals: SignalFrame,
        fusion_score: float,
        timestamp_s: float,
        rng: np.random.Generator | None = None,
    ) -> Optional[HardExample]:
        """对单帧做"是否值得挖掘"的判定。"""
        if not self._allow_window(timestamp_s):
            return None
        rng = rng or np.random.default_rng()
        if rng.random() > self.config.sample_rate:
            return None

        reason: str | None = None
        if abs(fusion_score - 0.5) < self.config.uncertainty_band:
            reason = "uncertainty"
        elif float(np.var(signals.as_tuple())) >= self.config.disagreement_var_min:
            reason = "disagreement"

        if reason is None:
            return None
        ex = HardExample(
            sample_id=f"hex_{stream_id}_{int(timestamp_s * 1000)}",
            stream_id=stream_id,
            timestamp_s=timestamp_s,
            fusion_score=fusion_score,
            signals=signals,
            reason=reason,
        )
        self._kept.append(ex)
        self._count_in_window += 1
        return ex

    def consider_event(
        self,
        ev: StateTransitionEvent,
        user_feedback: str | None = None,
    ) -> Optional[HardExample]:
        """对状态迁移事件考虑挖掘；用户反馈"误报"权重 ×3。"""
        weight = 1.0
        reason: str | None = None
        if user_feedback == "false_alarm" and ev.to_state in (
            StreamState.LONG_AWAY,
            StreamState.ALERT_ESCALATED,
        ):
            reason, weight = "user_feedback_false_alarm", 3.0
        elif user_feedback == "missed_alert":
            reason, weight = "user_feedback_missed", 5.0

        if reason is None:
            return None
        ex = HardExample(
            sample_id=ev.event_id,
            stream_id=ev.stream_id,
            timestamp_s=ev.timestamp_s,
            fusion_score=ev.fusion_score,
            signals=ev.signals,
            reason=reason,
            weight=weight,
        )
        self._kept.append(ex)
        return ex

    def drain(self) -> list[HardExample]:
        out, self._kept = self._kept, []
        return out

    def _allow_window(self, timestamp_s: float) -> bool:
        idx = int(timestamp_s // 60.0)
        if idx != self._window_index:
            self._window_index = idx
            self._count_in_window = 0
        return self._count_in_window < self.config.keep_max_per_minute


def aggregate_curriculum(
    examples: Iterable[HardExample],
    target_size: int = 1000,
) -> list[HardExample]:
    """从挖掘池里按权重抽样组装下一轮 fine-tune 训练集。"""
    pool = list(examples)
    if not pool:
        return []
    weights = np.asarray([e.weight for e in pool], dtype=np.float64)
    weights /= weights.sum()
    rng = np.random.default_rng(42)
    n = min(target_size, len(pool))
    idx = rng.choice(len(pool), size=n, replace=False, p=weights)
    return [pool[int(i)] for i in idx]
