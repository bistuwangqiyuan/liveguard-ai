"""
liveguard_algo.fusion.state_machine
===================================

主播在岗判定 · 决策融合状态机 (Deterministic Finite State Machine, DFSM)。

实现 ``Requirements REQ-ALGO-007 / REQ-SYS-002 / REQ-SYS-003``，对齐
``Design §6.1–§6.5``。

核心契约
--------

* 输入：每 200 ms 一个 :class:`SignalFrame`，6 个信号源 ∈ [0, 1]。
* 输出：每次 ``feed`` 返回 ``Optional[StateTransitionEvent]``；同状态返回 ``None``。
* 不可变状态转移日志：所有迁移可追溯到 (model_versions, signal breakdown, fusion score)。

设计要点
--------

1. **可解释性**：每条迁移记录信号贡献，便于审计与 SLA 违约根因分析。
2. **抗抖动 (hysteresis)**：upper=0.65/lower=0.35 + 5 s 累积窗。
3. **回退安全**：单信号置信过低 (< 0.3) 时权重折半，重新归一。
4. **零外部依赖**：纯 Python + ``numpy`` 可选 — 边缘 NPU 与 Lambda 均可运行。
5. **线程安全**：每个 `stream_id` 独立实例；类内部不共享可变状态。

使用示例
--------

>>> fsm = StreamFSM()
>>> for _ in range(30):
...     fsm.feed(SignalFrame(0.95, 0.90, 0.80, 0.95, 0.50, 0.70), dt=0.2)
>>> fsm.state
<StreamState.ON_DUTY: 'ON_DUTY'>
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Iterable, Optional
from uuid import uuid4

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class StreamState(str, Enum):
    """状态机状态枚举（持久化字符串值，便于跨服务一致）。"""

    IDLE = "IDLE"
    ON_DUTY = "ON_DUTY"
    BRIEF_AWAY = "BRIEF_AWAY"
    LONG_AWAY = "LONG_AWAY"
    ALERT_ESCALATED = "ALERT_ESCALATED"


# ---------------------------------------------------------------------------
# Signals & weights
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SignalFrame:
    """6 路多模态信号瞬时帧，全部 ∈ [0, 1]。

    任一字段缺失（信号源短暂失效）应传 0；如需"未知"语义请使用
    :class:`SignalFrame` 配套的置信度阈值传 0 同时附加 ``trust`` 元数据
    （在 :class:`FusionWeights.confidence_floor` 处理）。
    """

    face: float = 0.0
    person: float = 0.0
    reid: float = 0.0
    liveness: float = 0.0
    action: float = 0.0
    audio: float = 0.0

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.face, self.person, self.reid, self.liveness, self.action, self.audio)

    def __post_init__(self) -> None:
        for name, v in zip(self._fields(), self.as_tuple()):
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"signal {name}={v} 超出 [0,1]")

    @staticmethod
    def _fields() -> tuple[str, ...]:
        return ("face", "person", "reid", "liveness", "action", "audio")


@dataclass(frozen=True, slots=True)
class FusionWeights:
    """信号融合权重；和必须 = 1.0（或归一化）。"""

    face: float = 0.30
    person: float = 0.20
    reid: float = 0.20
    liveness: float = 0.10
    action: float = 0.10
    audio: float = 0.10
    confidence_floor: float = 0.30
    """单信号置信度低于此阈值时，权重将自动折半再做归一化。"""

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.face, self.person, self.reid, self.liveness, self.action, self.audio)

    def __post_init__(self) -> None:
        s = sum(self.as_tuple())
        if abs(s - 1.0) > 1e-6:
            raise ValueError(f"weights 和必须为 1.0，当前={s:.4f}")
        if not 0.0 <= self.confidence_floor <= 0.5:
            raise ValueError("confidence_floor 必须 ∈ [0, 0.5]")


DEFAULT_WEIGHTS = FusionWeights()
"""见 BP §4.3.2 的默认融合权重。"""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FSMConfig:
    """状态机阈值与时间常数。

    时间单位为秒；默认值与 ``Requirements §3 / Design §6.2`` 对齐。

    Attributes:
        upper_threshold: 复合得分 ≥ 此值进入 ON_DUTY 路径（hysteresis 上界）。
        lower_threshold: 复合得分 < 此值进入 AWAY 路径（hysteresis 下界）。
        consensus_window_s: 进入新状态需要在该窗口内连续满足条件的秒数。
        brief_to_long_s: 从 BRIEF_AWAY 升级到 LONG_AWAY 的累计离开秒数。
        long_to_escalate_s: 从 LONG_AWAY 升级到 ALERT_ESCALATED 的额外秒数。
    """

    upper_threshold: float = 0.65
    lower_threshold: float = 0.35
    consensus_window_s: float = 5.0
    brief_to_long_s: float = 60.0
    long_to_escalate_s: float = 120.0

    def __post_init__(self) -> None:
        if not 0.0 < self.lower_threshold < self.upper_threshold < 1.0:
            raise ValueError("阈值必须满足 0 < lower < upper < 1")
        if min(self.consensus_window_s, self.brief_to_long_s, self.long_to_escalate_s) <= 0:
            raise ValueError("时间常数必须为正")


DEFAULT_CONFIG = FSMConfig()


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StateTransitionEvent:
    """每次状态变化产出的可审计事件。

    序列化为 CloudEvents 1.0 详见 :mod:`liveguard_algo.fusion.explainer`。
    """

    event_id: str
    stream_id: str
    from_state: StreamState
    to_state: StreamState
    fusion_score: float
    signals: SignalFrame
    weights_used: tuple[float, float, float, float, float, float]
    timer_offline_s: float
    timestamp_s: float
    severity: str
    """``INFO`` / ``P1`` / ``P0``。决定 Notify Service 升级路径。"""

    extras: dict[str, object] = field(default_factory=dict)

    def severity_label(self) -> str:
        """便于 UI 直接显示的中文标签。"""
        return {"INFO": "正常", "P1": "需关注", "P0": "紧急"}.get(self.severity, self.severity)


# ---------------------------------------------------------------------------
# Stream FSM
# ---------------------------------------------------------------------------


_INFO = "INFO"
_P1 = "P1"
_P0 = "P0"


class StreamFSM:
    """单个直播流的决策融合状态机。

    线程模型：每个 `stream_id` 一个实例，串行喂入 SignalFrame；不可跨线程共享。

    Args:
        stream_id: 直播流的稳定唯一 ID（无关协议）。
        config: 阈值/时间常数。
        weights: 6 路信号的融合权重。

    Example:
        >>> fsm = StreamFSM(stream_id="s_demo")
        >>> evt = fsm.feed(SignalFrame(face=0.95, person=0.95,
        ...                            reid=0.85, liveness=0.95,
        ...                            action=0.50, audio=0.70), dt=0.2)
    """

    __slots__ = (
        "stream_id",
        "config",
        "weights",
        "_state",
        "_timer_offline_s",
        "_consensus_buf",
        "_clock_s",
        "_last_score",
        "_history",
    )

    def __init__(
        self,
        stream_id: str = "default",
        config: FSMConfig = DEFAULT_CONFIG,
        weights: FusionWeights = DEFAULT_WEIGHTS,
    ) -> None:
        self.stream_id: str = stream_id
        self.config: FSMConfig = config
        self.weights: FusionWeights = weights
        self._state: StreamState = StreamState.IDLE
        self._timer_offline_s: float = 0.0
        self._clock_s: float = 0.0
        self._last_score: float = 0.0
        # consensus buffer keeps recent (score, dt) for the configured window
        self._consensus_buf: Deque[tuple[float, float]] = deque()
        self._history: list[StateTransitionEvent] = []

    # ------------------------------------------------------------------ public

    @property
    def state(self) -> StreamState:
        return self._state

    @property
    def offline_seconds(self) -> float:
        return self._timer_offline_s

    @property
    def last_fusion_score(self) -> float:
        """最近一次 ``feed`` 的瞬时融合得分（0..1）。"""
        return self._last_score

    @property
    def history(self) -> list[StateTransitionEvent]:
        """只读拷贝。"""
        return list(self._history)

    def feed(self, signals: SignalFrame, dt: float) -> Optional[StateTransitionEvent]:
        """喂入一个信号帧并推进时间 ``dt`` 秒。

        Args:
            signals: 6 路多模态信号。
            dt: 距离上一次喂入的时间间隔（秒）。

        Returns:
            如果状态发生变化，返回 :class:`StateTransitionEvent`；否则 ``None``。
        """
        if dt <= 0:
            raise ValueError("dt 必须 > 0")
        self._clock_s += dt

        # 1. 信号置信度自适应权重
        adaptive_w = self._adaptive_weights(signals)
        score = sum(w * s for w, s in zip(adaptive_w, signals.as_tuple()))
        self._last_score = score
        self._consensus_buf.append((score, dt))
        self._trim_consensus_buf()

        # 2. 离线计时（在 BRIEF_AWAY/LONG_AWAY 中累加）
        if self._state in (StreamState.BRIEF_AWAY, StreamState.LONG_AWAY):
            self._timer_offline_s += dt

        # 3. 状态推进
        new_state = self._next_state(score)
        if new_state == self._state:
            return None

        return self._do_transition(new_state, signals, adaptive_w)

    # ------------------------------------------------------------------ helpers

    def _adaptive_weights(self, signals: SignalFrame) -> tuple[float, ...]:
        """confidence_floor 以下信号权重折半再归一。

        简化解释：
            如果某模型瞬时置信很低（如人脸完全遮挡），它的"投票权"应被弱化，
            避免误把 0 分被当作"主播在岗信号缺失"过度惩罚。
        """
        floor = self.weights.confidence_floor
        raw_w = list(self.weights.as_tuple())
        for i, s in enumerate(signals.as_tuple()):
            if s < floor:
                raw_w[i] *= 0.5
        total = sum(raw_w)
        if total == 0:  # pragma: no cover (理论上不会发生)
            return tuple(self.weights.as_tuple())
        return tuple(w / total for w in raw_w)

    def _trim_consensus_buf(self) -> None:
        window = self.config.consensus_window_s
        cumulative = 0.0
        # 保留至少覆盖 window 秒的最近样本
        for i in range(len(self._consensus_buf) - 1, -1, -1):
            cumulative += self._consensus_buf[i][1]
            if cumulative >= window:
                break
        # 删除窗口外的旧帧
        kept = list(self._consensus_buf)[-(len(self._consensus_buf) - i if i > 0 else 0):]
        self._consensus_buf = deque(kept) if kept else self._consensus_buf

    def _consensus_score(self) -> float:
        """加权平均得分（按 dt 加权）— 抗抖动。"""
        if not self._consensus_buf:
            return self._last_score
        total_dt = sum(dt for _, dt in self._consensus_buf)
        if total_dt == 0:  # pragma: no cover
            return self._last_score
        return sum(s * dt for s, dt in self._consensus_buf) / total_dt

    def _next_state(self, instantaneous_score: float) -> StreamState:
        cfg = self.config
        avg = self._consensus_score()

        # IDLE: 一旦看到任何"在岗"信号 → ON_DUTY
        if self._state == StreamState.IDLE:
            if instantaneous_score >= cfg.upper_threshold:
                return StreamState.ON_DUTY
            return StreamState.IDLE

        # ON_DUTY → BRIEF_AWAY (持续低分)
        if self._state == StreamState.ON_DUTY:
            if avg < cfg.lower_threshold and self._buffer_full():
                return StreamState.BRIEF_AWAY
            return StreamState.ON_DUTY

        # BRIEF_AWAY → ON_DUTY (恢复) 或 LONG_AWAY (超时)
        if self._state == StreamState.BRIEF_AWAY:
            if avg >= cfg.upper_threshold and self._buffer_full():
                return StreamState.ON_DUTY
            if self._timer_offline_s >= cfg.brief_to_long_s:
                return StreamState.LONG_AWAY
            return StreamState.BRIEF_AWAY

        # LONG_AWAY → ON_DUTY (恢复) 或 ALERT_ESCALATED (再超时)
        if self._state == StreamState.LONG_AWAY:
            if avg >= cfg.upper_threshold and self._buffer_full():
                return StreamState.ON_DUTY
            if self._timer_offline_s >= cfg.brief_to_long_s + cfg.long_to_escalate_s:
                return StreamState.ALERT_ESCALATED
            return StreamState.LONG_AWAY

        # ALERT_ESCALATED → ON_DUTY 仅当强信号持续 (cooldown 2× window)
        if self._state == StreamState.ALERT_ESCALATED:
            if avg >= cfg.upper_threshold and self._buffer_covers(2 * cfg.consensus_window_s):
                return StreamState.ON_DUTY
            return StreamState.ALERT_ESCALATED

        return self._state  # pragma: no cover (defensive)

    def _buffer_full(self) -> bool:
        total_dt = sum(dt for _, dt in self._consensus_buf)
        return total_dt >= self.config.consensus_window_s

    def _buffer_covers(self, seconds: float) -> bool:
        total_dt = sum(dt for _, dt in self._consensus_buf)
        return total_dt >= seconds

    def _do_transition(
        self,
        new_state: StreamState,
        signals: SignalFrame,
        adaptive_w: tuple[float, ...],
    ) -> StateTransitionEvent:
        old_state = self._state
        # 状态切换业务规则
        severity = _severity_for(new_state, old_state)

        # 重置离线计时器：返回 ON_DUTY 时清零
        if new_state == StreamState.ON_DUTY:
            self._timer_offline_s = 0.0

        ev = StateTransitionEvent(
            event_id=f"evt_{uuid4().hex[:24]}",
            stream_id=self.stream_id,
            from_state=old_state,
            to_state=new_state,
            fusion_score=round(self._last_score, 6),
            signals=signals,
            weights_used=tuple(round(w, 6) for w in adaptive_w),
            timer_offline_s=round(self._timer_offline_s, 3),
            timestamp_s=round(self._clock_s, 3),
            severity=severity,
        )
        self._state = new_state
        self._history.append(ev)
        return ev


def _severity_for(to_state: StreamState, from_state: StreamState) -> str:
    """状态迁移到事件严重级映射。"""
    if to_state == StreamState.ALERT_ESCALATED:
        return _P0
    if to_state == StreamState.LONG_AWAY:
        return _P1
    # 任何回到 ON_DUTY 都是好消息（INFO）
    return _INFO


# ---------------------------------------------------------------------------
# Convenience: batch feed
# ---------------------------------------------------------------------------


def replay(
    fsm: StreamFSM,
    frames: Iterable[tuple[SignalFrame, float]],
) -> list[StateTransitionEvent]:
    """批量回放（用于离线分析、回归测试、压测）。"""
    out: list[StateTransitionEvent] = []
    for sig, dt in frames:
        ev = fsm.feed(sig, dt)
        if ev is not None:
            out.append(ev)
    return out
