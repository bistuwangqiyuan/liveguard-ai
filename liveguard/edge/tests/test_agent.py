"""Edge Agent 冒烟测试 — 合成源驱动 Pipeline 并模拟上行。"""

from __future__ import annotations

import httpx
import pytest

from liveguard_edge.agent import AgentConfig, EdgeAgent
from liveguard_edge.source import SyntheticSource
from liveguard_edge.uploader import SignalUploader, UploaderConfig


@pytest.mark.asyncio
async def test_agent_runs_and_uploads(httpx_mock) -> None:
    httpx_mock.add_response(
        url="http://backend.test/v1/ingest/signals",
        method="POST",
        json={"stream_id": "s_edge_1", "state": "ON_DUTY", "fusion_score": 0.9, "offline_seconds": 0.0,
              "state_event": None, "cheat_flags": []},
        is_reusable=True,
    )
    up = SignalUploader(UploaderConfig(base_url="http://backend.test", token="t", max_retries=1))
    src = SyntheticSource(fps=5, n_frames=10, blank_after=None)
    agent = EdgeAgent(
        AgentConfig(stream_id="s_edge_1", tenant_id="t_demo", agent_id="edge-unit"),
        source=src, uploader=up,
    )
    try:
        m = await agent.run(max_frames=10)
    finally:
        await up.aclose()
        src.close()

    assert m.frames_processed == 10
    assert m.uploads_ok >= 1
    assert m.last_fusion_score > 0.0
