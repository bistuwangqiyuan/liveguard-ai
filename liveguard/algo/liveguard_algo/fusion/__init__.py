"""融合决策子包：DFSM + 反作弊状态机 + 可解释性。"""

from .cheat_fsm import CheatFSM, CheatFlag, CheatPattern, CheatSignals
from .explainer import ExplanationReport, explain_event
from .state_machine import (
    DEFAULT_WEIGHTS,
    FSMConfig,
    FusionWeights,
    SignalFrame,
    StateTransitionEvent,
    StreamFSM,
    StreamState,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "CheatFSM",
    "CheatFlag",
    "CheatPattern",
    "CheatSignals",
    "ExplanationReport",
    "FSMConfig",
    "FusionWeights",
    "SignalFrame",
    "StateTransitionEvent",
    "StreamFSM",
    "StreamState",
    "explain_event",
]
