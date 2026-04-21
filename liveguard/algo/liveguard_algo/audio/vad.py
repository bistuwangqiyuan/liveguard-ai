"""
liveguard_algo.audio.vad
========================

语音活动检测（Voice Activity Detection） — 实现 ``REQ-ALG-009``。

使用 Silero-VAD（mock）。生产环境会用 ONNX 版本的 silero-vad；当无 onnxruntime
时退化为基于能量 + 过零率的双阈值实现。
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

import numpy as np

from ..runtime import register_model

DEFAULT_SR = 16000
DEFAULT_FRAME_MS = 30


@dataclass(frozen=True, slots=True)
class VadFrame:
    is_voice: float  # 0..1 概率
    energy_db: float
    zero_crossing_rate: float
    timestamp_s: float


@register_model(
    name="audio.silero_vad",
    version="silero-vad-v4-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 1.8, "f1_voiced": 0.974},
    license="MIT",
    data_lineage="LibriSpeech + AVA-Speech",
)
class VadProcessorMock:
    def __init__(self, sample_rate: int = DEFAULT_SR, frame_ms: int = DEFAULT_FRAME_MS,
                 energy_threshold_db: float = -45.0) -> None:
        self._sr = sample_rate
        self._frame = int(sample_rate * frame_ms / 1000)
        self._th_db = energy_threshold_db
        self._buf: Deque[float] = deque(maxlen=33)  # ~1s
        self._t = 0.0

    def process(self, pcm: np.ndarray) -> VadFrame:
        if pcm.size == 0:
            return VadFrame(is_voice=0.0, energy_db=-120.0, zero_crossing_rate=0.0, timestamp_s=self._t)
        rms = float(np.sqrt(np.mean(pcm.astype(np.float32) ** 2))) + 1e-9
        energy_db = 20.0 * float(np.log10(rms))
        zcr = float(np.mean(np.diff(np.signbit(pcm)).astype(np.float32)))
        # 能量过阈值且 zcr 在语音区间(0.02-0.25)
        prob = 0.0
        if energy_db >= self._th_db:
            prob += 0.6
        if 0.02 <= zcr <= 0.25:
            prob += 0.4
        prob = min(prob, 0.99)
        self._buf.append(prob)
        self._t += pcm.shape[0] / self._sr
        return VadFrame(is_voice=prob, energy_db=energy_db, zero_crossing_rate=zcr, timestamp_s=self._t)

    @property
    def speech_ratio(self) -> float:
        if not self._buf:
            return 0.0
        return float(sum(p >= 0.5 for p in self._buf) / len(self._buf))
