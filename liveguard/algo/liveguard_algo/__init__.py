"""
liveguard_algo
==============

守播 LiveGuard AI · 多模态算法引擎。

Public surface:

    >>> from liveguard_algo import StreamFSM, SignalFrame, FusionWeights
    >>> fsm = StreamFSM()
    >>> ev = fsm.feed(SignalFrame(face=0.0, person=0.0, reid=0.0,
    ...                          liveness=0.0, action=0.05, audio=0.0), dt=0.2)

See :mod:`liveguard_algo.fusion.state_machine` for the definitive contract.
"""

from __future__ import annotations

from .fusion import (
    DEFAULT_WEIGHTS,
    CheatFlag,
    CheatFSM,
    CheatPattern,
    CheatSignals,
    ExplanationReport,
    FSMConfig,
    FusionWeights,
    SignalFrame,
    StateTransitionEvent,
    StreamFSM,
    StreamState,
    explain_event,
)
from .pipeline import LiveGuardPipeline, PipelineConfig, PipelineFrameResult
from .runtime import MODEL_REGISTRY, ModelMetadata

__all__ = [
    "DEFAULT_WEIGHTS",
    "CheatFSM",
    "CheatFlag",
    "CheatPattern",
    "CheatSignals",
    "ExplanationReport",
    "FSMConfig",
    "FusionWeights",
    "LiveGuardPipeline",
    "MODEL_REGISTRY",
    "ModelMetadata",
    "PipelineConfig",
    "PipelineFrameResult",
    "SignalFrame",
    "StateTransitionEvent",
    "StreamFSM",
    "StreamState",
    "explain_event",
]

__version__ = "1.0.0"
