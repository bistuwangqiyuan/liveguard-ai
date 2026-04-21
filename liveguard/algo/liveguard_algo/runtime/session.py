"""
liveguard_algo.runtime.session
==============================

ONNX / TensorRT / Torch 抽象推理 session。

设计目标：
* 统一接口 ``run(inputs: dict) -> dict``，与具体后端解耦。
* 在没有 onnxruntime/torch 时自动 fallback 到 :class:`MockSession`，使核心逻辑
  能在 CI / 离线环境跑测试。
* 全部推理调用都返回 latency_ms 计量，写入 OTel span（外层 wrapper 处理）。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import onnxruntime as ort  # type: ignore
    _HAS_ORT = True
except ImportError:  # pragma: no cover
    _HAS_ORT = False


@dataclass(slots=True)
class InferenceResult:
    outputs: dict[str, np.ndarray]
    latency_ms: float
    backend: str


class InferenceSession(ABC):
    """抽象推理 session。"""

    @abstractmethod
    def run(self, inputs: dict[str, np.ndarray]) -> InferenceResult: ...

    @abstractmethod
    def warmup(self, n: int = 3) -> None: ...

    @property
    @abstractmethod
    def backend(self) -> str: ...


class OnnxSession(InferenceSession):
    """基于 onnxruntime 的实现。"""

    def __init__(self, model_path: str, providers: list[str] | None = None) -> None:
        if not _HAS_ORT:
            raise RuntimeError("onnxruntime not installed; install liveguard-algo[infer].")
        self._sess = ort.InferenceSession(  # type: ignore[union-attr]
            model_path,
            providers=providers or ["CPUExecutionProvider"],
        )
        self._inputs = [i.name for i in self._sess.get_inputs()]
        self._outputs = [o.name for o in self._sess.get_outputs()]

    @property
    def backend(self) -> str:
        return "onnxruntime"

    def warmup(self, n: int = 3) -> None:
        dummy = {
            i.name: np.zeros([d if isinstance(d, int) and d > 0 else 1 for d in i.shape], dtype=np.float32)
            for i in self._sess.get_inputs()
        }
        for _ in range(n):
            self._sess.run(self._outputs, dummy)

    def run(self, inputs: dict[str, np.ndarray]) -> InferenceResult:
        t0 = time.perf_counter()
        out = self._sess.run(self._outputs, inputs)
        elapsed = (time.perf_counter() - t0) * 1000.0
        return InferenceResult(
            outputs=dict(zip(self._outputs, out)),
            latency_ms=elapsed,
            backend=self.backend,
        )


class MockSession(InferenceSession):
    """确定性 mock，用于单元测试和无 GPU 环境的 demo。"""

    def __init__(self, model_name: str, output_shapes: dict[str, tuple[int, ...]] | None = None,
                 seed: int = 42, latency_ms: float = 8.0) -> None:
        self._name = model_name
        self._shapes = output_shapes or {}
        self._rng = np.random.default_rng(seed)
        self._latency = latency_ms

    @property
    def backend(self) -> str:
        return f"mock:{self._name}"

    def warmup(self, n: int = 3) -> None:
        return

    def run(self, inputs: dict[str, np.ndarray]) -> InferenceResult:
        outputs = {
            k: self._rng.random(shape, dtype=np.float32)
            for k, shape in self._shapes.items()
        } or {"score": self._rng.random((1,), dtype=np.float32)}
        return InferenceResult(outputs=outputs, latency_ms=self._latency, backend=self.backend)


def get_session(model_path: str | None = None, *, mock_for: str | None = None,
                output_shapes: dict[str, tuple[int, ...]] | None = None) -> InferenceSession:
    """工厂：优先 ONNX，否则 mock。"""
    if model_path and _HAS_ORT:
        return OnnxSession(model_path)
    return MockSession(model_name=mock_for or "unknown", output_shapes=output_shapes)
