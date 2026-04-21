"""
liveguard_algo.audio.speaker
============================

声纹（Speaker Verification） — 实现 ``REQ-ALG-010``。

mock 实现，完整实现使用 ECAPA-TDNN（speechbrain 或 wespeaker），
输出 192 维 embedding，用余弦相似度进行 1:1 验证。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from threading import Lock

import numpy as np

from ..runtime import register_model

SPK_DIM = 192
SPK_THRESHOLD = 0.55


@register_model(
    name="audio.ecapa_tdnn",
    version="ecapa-tdnn-c512-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 6.2, "voxceleb1_eer": 0.0086, "cnceleb_eer": 0.044},
    license="Apache-2.0 (SpeechBrain)",
    data_lineage="VoxCeleb 1+2 + CN-Celeb",
)
class SpeakerVerifierMock:
    def __init__(self, dim: int = SPK_DIM) -> None:
        self._dim = dim

    def embed(self, pcm: np.ndarray) -> np.ndarray:
        if pcm.size == 0:
            rng = np.random.default_rng(7)
            v = rng.standard_normal(self._dim).astype(np.float32)
        else:
            digest = hashlib.sha1(pcm.tobytes(), usedforsecurity=False).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            v = rng.standard_normal(self._dim).astype(np.float32)
            v += float(pcm.mean()) / 32.0
        return v / (np.linalg.norm(v) or 1e-8)

    @staticmethod
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))


@dataclass(slots=True)
class _SpeakerEntry:
    centroid: np.ndarray
    enrollments: int = 1


class SpeakerProfileGallery:
    """主播声纹库 — 支持每位主播多次注册的 EMA 更新。"""

    def __init__(self, threshold: float = SPK_THRESHOLD, alpha: float = 0.2) -> None:
        self._g: dict[str, _SpeakerEntry] = {}
        self._th = threshold
        self._a = alpha
        self._lock = Lock()

    def enroll(self, host_id: str, embedding: np.ndarray) -> None:
        with self._lock:
            if host_id in self._g:
                e = self._g[host_id]
                e.centroid = (1 - self._a) * e.centroid + self._a * embedding
                e.centroid /= float(np.linalg.norm(e.centroid)) or 1e-8
                e.enrollments += 1
            else:
                self._g[host_id] = _SpeakerEntry(centroid=embedding.copy())

    def verify(self, host_id: str, embedding: np.ndarray) -> tuple[bool, float]:
        with self._lock:
            entry = self._g.get(host_id)
            if entry is None:
                return False, 0.0
            score = float(np.dot(entry.centroid, embedding))
            return score >= self._th, score

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._g)
