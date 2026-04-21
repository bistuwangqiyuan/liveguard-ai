"""活体检测：rPPG + 时序一致性 + Deepfake 双流。"""
from .liveness import LivenessResult, LivenessScorerMock

__all__ = ["LivenessResult", "LivenessScorerMock"]
