"""
liveguard_edge.agent
====================

Edge Agent — 把视频源 → algo pipeline → uploader 串起来。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import structlog
from liveguard_algo import LiveGuardPipeline, PipelineConfig

from .source import Frame, VideoSource
from .uploader import SignalUploader

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class AgentConfig:
    stream_id: str
    tenant_id: str
    host_id: str = "host-unknown"
    agent_id: str = "edge-0"
    upload_every_n_frames: int = 1
    heartbeat_every_s: float = 30.0
    privacy_mode: bool = True
    """隐私模式下 pipeline 可配置不输出原始图像，此处仅为标注。"""


@dataclass(slots=True)
class AgentMetrics:
    frames_processed: int = 0
    uploads_ok: int = 0
    uploads_fail: int = 0
    last_state: str = "IDLE"
    last_fusion_score: float = 0.0
    last_latency_ms: float = 0.0
    started_at: float = field(default_factory=time.time)


class EdgeAgent:
    def __init__(
        self,
        cfg: AgentConfig,
        source: VideoSource,
        uploader: SignalUploader,
        pipeline_config: PipelineConfig | None = None,
    ) -> None:
        self.cfg = cfg
        self.src = source
        self.up = uploader
        self.pipe = LiveGuardPipeline(
            stream_id=cfg.stream_id, host_id=cfg.host_id, config=pipeline_config
        )
        self.metrics = AgentMetrics()
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    async def run(self, *, max_frames: Optional[int] = None) -> AgentMetrics:
        """驱动单流处理；``max_frames`` 限额主要给 CI。"""
        n = 0
        for frame in self.src:
            if self._stop.is_set():
                break
            await self._process_frame(frame)
            n += 1
            if max_frames is not None and n >= max_frames:
                break
            # 让出事件循环 — 避免饿死其它协程
            await asyncio.sleep(0)
        return self.metrics

    async def _process_frame(self, frame: Frame) -> None:
        img: np.ndarray | None = frame.image
        result = self.pipe.process(img, frame.pcm, dt=frame.dt, timestamp_s=frame.timestamp_s)
        self.metrics.frames_processed += 1
        self.metrics.last_state = result.signals  # placeholder — replaced below
        sig = result.signals
        self.metrics.last_fusion_score = result.fusion_score
        self.metrics.last_latency_ms = result.latency_ms

        if self.metrics.frames_processed % max(1, self.cfg.upload_every_n_frames) != 0:
            return

        payload = {
            "stream_id": self.cfg.stream_id,
            "ts_ms": int(frame.timestamp_s * 1000),
            "face": sig.face,
            "person": sig.person,
            "reid": sig.reid,
            "liveness": sig.liveness,
            "action": sig.action,
            "audio": sig.audio,
            "deepfake": result.debug.get("deepfake", 0.0),
            "reid_similarity": result.debug.get("reid_similarity", 1.0),
            "temporal_var": result.debug.get("temporal_var", 0.5),
            "screen_replay": result.debug.get("screen_replay", 0.0),
            "edge_agent_id": self.cfg.agent_id,
        }
        try:
            ack = await self.up.upload(payload)
            if ack.get("ok"):
                self.metrics.uploads_ok += 1
                self.metrics.last_state = ack.get("state", self.metrics.last_state)
            else:
                self.metrics.uploads_fail += 1
        except Exception as exc:  # noqa: BLE001
            self.metrics.uploads_fail += 1
            log.error("edge.upload_failed", exc=str(exc))
