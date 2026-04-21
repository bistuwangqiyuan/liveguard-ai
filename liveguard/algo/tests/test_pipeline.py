"""集成测试：完整的 :class:`LiveGuardPipeline` 流水线。"""

from __future__ import annotations

import numpy as np
import pytest

from liveguard_algo import (
    LiveGuardPipeline,
    SignalFrame,
    StreamFSM,
    StreamState,
)
from liveguard_algo.fusion.explainer import explain_event, to_cloudevent


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(2026)


def _make_active_frame(rng: np.random.Generator) -> np.ndarray:
    # 高方差合成帧（彩色棋盘 + 噪声）— 让 mock 检测器产生高分。
    h, w = 240, 320
    yy, xx = np.mgrid[0:h, 0:w]
    base = ((xx // 16 + yy // 16) % 2) * 200 + 30
    noise = rng.integers(0, 60, size=(h, w), dtype=np.int16)
    plane = np.clip(base + noise, 0, 255).astype(np.uint8)
    return np.stack([plane, np.flipud(plane), np.fliplr(plane)], axis=2)


def _make_blank_frame() -> np.ndarray:
    return np.zeros((240, 320, 3), dtype=np.uint8)


def _make_voice(rng: np.random.Generator) -> np.ndarray:
    t = np.linspace(0, 1, 16000, dtype=np.float32)
    return (0.3 * np.sin(2 * np.pi * 220 * t) + 0.05 * rng.standard_normal(t.size)).astype(np.float32)


def test_pipeline_smoke_active_video_then_blank(rng: np.random.Generator) -> None:
    pipe = LiveGuardPipeline(stream_id="s_test", host_id="h_demo")
    transitions: list = []
    for _ in range(40):
        r = pipe.process(_make_active_frame(rng), _make_voice(rng), dt=0.2)
        if r.state_event:
            transitions.append(r.state_event)
    assert pipe.stream_fsm.state == StreamState.ON_DUTY
    for _ in range(80):
        r = pipe.process(_make_blank_frame(), None, dt=0.5)
        if r.state_event:
            transitions.append(r.state_event)
    states = [e.to_state for e in transitions]
    assert StreamState.ON_DUTY in states
    assert any(s in {StreamState.BRIEF_AWAY, StreamState.LONG_AWAY, StreamState.ALERT_ESCALATED} for s in states)


def test_explainer_event_to_cloudevent() -> None:
    fsm = StreamFSM(stream_id="s_demo")
    ev = fsm.feed(SignalFrame(0.95, 0.95, 0.9, 0.95, 0.5, 0.7), dt=0.2)
    assert ev is not None
    report = explain_event(ev)
    assert report.headline
    assert len(report.contributions) == 6
    ce = to_cloudevent(ev, tenant_id="t_acme", host_id="h_alice", platform="douyin")
    assert ce["specversion"] == "1.0"
    assert ce["data"]["stream_id"] == "s_demo"
    assert "fusion_score" in ce["data"]
