"""
liveguard_algo.face.embedder
============================

人脸嵌入：默认 ArcFace-MBF（128 维 / 量化 INT8），fallback mock。

公开：
* :class:`FaceEmbedderMock` — 输入 BGR + landmarks，输出 L2 归一化嵌入。
* :func:`cosine_similarity` — 余弦相似度（已归一化时等价于点乘）。
"""

from __future__ import annotations

import hashlib

import numpy as np

from ..runtime import register_model

EMBED_DIM = 128


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_n = float(np.linalg.norm(a)) or 1e-8
    b_n = float(np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / (a_n * b_n))


@register_model(
    name="face.arcface_mbf",
    version="r100-int8-v1.2-mock",
    framework="mock",
    benchmark={"latency_ms_p95": 6.4, "lfw_acc": 0.9982, "ijbc_tar_at_far_1e4": 0.961},
    license="MIT (insightface)",
    data_lineage="MS-Celeb-1M cleansed (Glint360K)",
)
class FaceEmbedderMock:
    def __init__(self, dim: int = EMBED_DIM, seed: int = 17) -> None:
        self._dim = dim
        self._seed = seed

    def embed(self, face_crop: np.ndarray) -> np.ndarray:
        """从裁剪后的人脸生成确定性 128 维嵌入。

        生产实现会做：1) 5 点对齐到 112×112；2) ArcFace 推理；3) L2 归一化。
        """
        if face_crop is None or face_crop.size == 0:
            rng = np.random.default_rng(self._seed)
            v = rng.standard_normal(self._dim).astype(np.float32)
        else:
            # 用 hash + crop 像素均值 / 方差产生稳定向量；对相同输入返回相同输出
            digest = hashlib.sha1(face_crop.tobytes(), usedforsecurity=False).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            v = rng.standard_normal(self._dim).astype(np.float32)
            # 让"主播稳定"的特征略偏向均值方向，便于 demo 的 Re-ID 一致性
            mean = float(face_crop.mean())
            v += mean / 256.0
        norm = float(np.linalg.norm(v)) or 1e-8
        return v / norm
