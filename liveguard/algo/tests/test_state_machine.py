"""单元测试：决策融合状态机 :mod:`liveguard_algo.fusion.state_machine`。"""

from __future__ import annotations

import pytest

from liveguard_algo import (
    DEFAULT_WEIGHTS,
    FSMConfig,
    FusionWeights,
    SignalFrame,
    StreamFSM,
    StreamState,
)
from liveguard_algo.fusion.state_machine import replay


# ---------------------------------------------------------------------------
# SignalFrame & FusionWeights validation
# ---------------------------------------------------------------------------


def test_signal_frame_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        SignalFrame(face=1.2)
    with pytest.raises(ValueError):
        SignalFrame(audio=-0.01)


def test_fusion_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError):
        FusionWeights(face=0.5, person=0.6, reid=0.0, liveness=0.0, action=0.0, audio=0.0)


def test_default_weights_sum_to_one() -> None:
    assert sum(DEFAULT_WEIGHTS.as_tuple()) == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# State transitions — happy path
# ---------------------------------------------------------------------------


def _strong_signal() -> SignalFrame:
    return SignalFrame(face=0.95, person=0.92, reid=0.88, liveness=0.93, action=0.55, audio=0.70)


def _weak_signal() -> SignalFrame:
    return SignalFrame(face=0.0, person=0.0, reid=0.0, liveness=0.0, action=0.0, audio=0.0)


def test_idle_to_on_duty_on_strong_signal() -> None:
    fsm = StreamFSM()
    ev = fsm.feed(_strong_signal(), dt=0.2)
    assert ev is not None
    assert ev.from_state == StreamState.IDLE
    assert ev.to_state == StreamState.ON_DUTY
    assert ev.severity == "INFO"
    assert fsm.last_fusion_score >= 0.65


def test_on_duty_to_brief_away_after_consensus_window() -> None:
    cfg = FSMConfig(consensus_window_s=2.0, brief_to_long_s=10.0, long_to_escalate_s=10.0)
    fsm = StreamFSM(config=cfg)
    fsm.feed(_strong_signal(), dt=0.2)
    transitions = []
    for _ in range(20):  # 4 s 弱信号
        ev = fsm.feed(_weak_signal(), dt=0.2)
        if ev:
            transitions.append(ev)
    states = [t.to_state for t in transitions]
    assert StreamState.BRIEF_AWAY in states


def test_long_away_escalates_to_p0() -> None:
    cfg = FSMConfig(consensus_window_s=1.0, brief_to_long_s=2.0, long_to_escalate_s=2.0)
    fsm = StreamFSM(config=cfg)
    fsm.feed(_strong_signal(), dt=0.2)
    for _ in range(60):  # 12s 弱信号
        fsm.feed(_weak_signal(), dt=0.2)
    severities = [e.severity for e in fsm.history]
    assert "P1" in severities
    assert "P0" in severities
    assert fsm.state == StreamState.ALERT_ESCALATED


def test_recovery_resets_offline_timer() -> None:
    cfg = FSMConfig(consensus_window_s=1.0, brief_to_long_s=2.0, long_to_escalate_s=2.0)
    fsm = StreamFSM(config=cfg)
    fsm.feed(_strong_signal(), dt=0.2)
    for _ in range(15):  # 3s 离开 → BRIEF/LONG
        fsm.feed(_weak_signal(), dt=0.2)
    for _ in range(15):
        fsm.feed(_strong_signal(), dt=0.2)
    assert fsm.state == StreamState.ON_DUTY
    assert fsm.offline_seconds == 0.0


def test_replay_helper_yields_only_transitions() -> None:
    fsm = StreamFSM()
    frames = [(_strong_signal(), 0.2)] * 5 + [(_weak_signal(), 0.2)] * 50
    events = replay(fsm, frames)
    transitions = {(e.from_state, e.to_state) for e in events}
    assert (StreamState.IDLE, StreamState.ON_DUTY) in transitions


def test_low_confidence_signal_is_downweighted() -> None:
    fsm = StreamFSM()
    # face=0.25 (低于 floor 0.3) 应被折半，但 person/reid 还是高
    sig = SignalFrame(face=0.25, person=0.95, reid=0.90, liveness=0.85, action=0.5, audio=0.7)
    ev = fsm.feed(sig, dt=0.2)
    assert ev is not None
    assert ev.weights_used[0] < DEFAULT_WEIGHTS.face  # face 权重被折半


def test_dt_must_be_positive() -> None:
    fsm = StreamFSM()
    with pytest.raises(ValueError):
        fsm.feed(_strong_signal(), dt=0.0)
