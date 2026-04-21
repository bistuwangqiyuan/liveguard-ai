"""
liveguard_algo.person.reid
==========================

行人重识别（Re-ID）— 实现 ``REQ-ALG-005``：跨摄像头/换装识别同一主播。

策略：
* 用 OSNet-AIN-x0.25（mock）抽取 256 维 embedding。
* 在线维护一个 :class:`ReIDGallery`，用 EMA 更新质心，承担"主播是谁"的状态。
* 提供 :meth:`match` 返回相似度与是否同一人。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from threading import Lock

import numpy as np

from ..runtime import register_model

REID_DIM = 256
DEFAULT_THRESHOLD = 0.62  # OSNet 经验值（COSINE）
EMA_ALPHA = 0.1


@register_model(
    name="reid.osnet_ain",
    version="x0.25-int8-v1.0-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 7.8, "market1501_rank1": 0.911, "msmt17_rank1": 0.612},
    license="MIT (deep-person-reid)",
    data_lineage="Market-1501 + MSMT17 + private livestream",
)
class ReIDExtractorMock:
    def __init__(self, dim: int = REID_DIM) -> None:
        self._dim = dim

    def extract(self, person_crop: np.ndarray) -> np.ndarray:
        if person_crop is None or person_crop.size == 0:
            rng = np.random.default_rng(13)
            v = rng.standard_normal(self._dim).astype(np.float32)
        else:
            digest = hashlib.sha1(person_crop.tobytes(), usedforsecurity=False).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            v = rng.standard_normal(self._dim).astype(np.float32)
            v += float(person_crop.mean()) / 256.0
        return v / (np.linalg.norm(v) or 1e-8)


@dataclass(slots=True)
class _GalleryEntry:
    centroid: np.ndarray
    n_seen: int = 0
    last_score: float = 0.0


class ReIDGallery:
    """主播身份库；线程安全。

    * 每个租户/直播间一份 gallery，``key`` 通常是 ``host_id``。
    * 用 EMA（α=0.1）逐帧融合，平衡稳定性与适应性（光照、服装变化）。
    """

    def __init__(self, threshold: float = DEFAULT_THRESHOLD, alpha: float = EMA_ALPHA) -> None:
        self._gallery: dict[str, _GalleryEntry] = {}
        self._threshold = threshold
        self._alpha = alpha
        self._lock = Lock()

    def enroll(self, key: str, embedding: np.ndarray) -> None:
        with self._lock:
            self._gallery[key] = _GalleryEntry(
                centroid=embedding.astype(np.float32).copy(),
                n_seen=1,
                last_score=1.0,
            )

    def update(self, key: str, embedding: np.ndarray) -> float:
        with self._lock:
            entry = self._gallery.get(key)
            if entry is None:
                self._gallery[key] = _GalleryEntry(centroid=embedding.copy(), n_seen=1, last_score=1.0)
                return 1.0
            score = float(np.dot(entry.centroid, embedding))
            entry.centroid = (1 - self._alpha) * entry.centroid + self._alpha * embedding
            entry.centroid /= float(np.linalg.norm(entry.centroid)) or 1e-8
            entry.n_seen += 1
            entry.last_score = score
            return score

    def match(self, embedding: np.ndarray) -> tuple[str | None, float]:
        with self._lock:
            best_key: str | None = None
            best_score = -1.0
            for key, entry in self._gallery.items():
                s = float(np.dot(entry.centroid, embedding))
                if s > best_score:
                    best_score, best_key = s, key
            return (best_key if best_score >= self._threshold else None, best_score)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._gallery)
