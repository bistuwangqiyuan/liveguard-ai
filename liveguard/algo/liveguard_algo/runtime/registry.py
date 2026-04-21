"""
liveguard_algo.runtime.registry
===============================

模型注册表 — 实现 ``Design §5.1``。

每个模型在导入时注册元数据；用于：
* 推理 session 自动选择
* 审计追溯（事件 → model_version）
* 灰度发布与回滚（通过版本字符串 pin）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    name: str
    version: str
    framework: str  # "onnx" | "torch" | "tensorrt" | "mock"
    hash_sha256: str = ""
    input_spec: tuple[tuple[str, tuple[int, ...], str], ...] = ()
    output_spec: tuple[tuple[str, tuple[int, ...], str], ...] = ()
    inference_target: tuple[str, ...] = ("cpu",)
    benchmark: dict[str, float] = field(default_factory=dict)
    license: str = "Apache-2.0"
    data_lineage: str = ""
    artifact_uri: str = ""

    @property
    def fqn(self) -> str:
        return f"{self.name}@{self.version}"


# Single global registry — process-local; multi-process shares via Redis cache (out of scope for this module).
MODEL_REGISTRY: dict[str, ModelMetadata] = {}


def register_model(
    *,
    name: str,
    version: str,
    framework: str = "onnx",
    hash_sha256: str = "",
    input_spec: tuple[tuple[str, tuple[int, ...], str], ...] = (),
    output_spec: tuple[tuple[str, tuple[int, ...], str], ...] = (),
    inference_target: tuple[str, ...] = ("cpu",),
    benchmark: dict[str, float] | None = None,
    license: str = "Apache-2.0",
    data_lineage: str = "",
    artifact_uri: str = "",
) -> Callable[[T], T]:
    """装饰器：注册一个模型类/工厂。

    Example:
        >>> @register_model(name="face.scrfd", version="2.5g-v1.4", framework="onnx",
        ...                 benchmark={"latency_ms_p95": 12.1, "precision": 0.982})
        ... class SCRFDFaceDetector: ...
    """

    def _decorator(cls: T) -> T:
        meta = ModelMetadata(
            name=name,
            version=version,
            framework=framework,
            hash_sha256=hash_sha256,
            input_spec=input_spec,
            output_spec=output_spec,
            inference_target=inference_target,
            benchmark=benchmark or {},
            license=license,
            data_lineage=data_lineage,
            artifact_uri=artifact_uri,
        )
        MODEL_REGISTRY[meta.fqn] = meta
        # 把 metadata 挂到类上，便于运行时反查
        setattr(cls, "__lvg_meta__", meta)
        return cls

    return _decorator


def get_metadata(fqn: str) -> ModelMetadata:
    if fqn not in MODEL_REGISTRY:
        raise KeyError(f"Model not registered: {fqn}. Available: {sorted(MODEL_REGISTRY)}")
    return MODEL_REGISTRY[fqn]


def list_versions(name: str) -> list[ModelMetadata]:
    return sorted(
        (m for m in MODEL_REGISTRY.values() if m.name == name),
        key=lambda m: m.version,
    )


def to_audit_payload(fqn: str) -> dict[str, Any]:
    """便于审计写入的简短 dict。"""
    m = get_metadata(fqn)
    return {
        "name": m.name,
        "version": m.version,
        "framework": m.framework,
        "hash": m.hash_sha256[:12] if m.hash_sha256 else "",
        "license": m.license,
    }
