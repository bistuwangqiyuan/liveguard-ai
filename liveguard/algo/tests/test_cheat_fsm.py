"""单元测试：反作弊状态机 :mod:`liveguard_algo.fusion.cheat_fsm`。"""

from __future__ import annotations

from liveguard_algo.fusion import CheatFSM, CheatPattern, CheatSignals


def test_static_photo_detected_after_window() -> None:
    fsm = CheatFSM()
    flags: list = []
    for _ in range(60):  # 6s
        flags.extend(
            fsm.feed(CheatSignals(liveness_score=0.10, temporal_coherence_var=0.0), dt=0.1)
        )
    assert any(f.pattern == CheatPattern.STATIC_PHOTO for f in flags)


def test_deepfake_pattern_immediate() -> None:
    fsm = CheatFSM()
    flags = fsm.feed(CheatSignals(deepfake_score=0.9, liveness_score=0.4), dt=0.2)
    assert any(f.pattern == CheatPattern.DEEPFAKE_AVATAR for f in flags)


def test_impersonation_after_sustained_low_reid() -> None:
    fsm = CheatFSM()
    flags: list = []
    for _ in range(120):
        flags.extend(fsm.feed(CheatSignals(reid_similarity=0.30), dt=0.1))
    assert any(f.pattern == CheatPattern.IMPERSONATION for f in flags)


def test_normal_signals_no_flag() -> None:
    fsm = CheatFSM()
    for _ in range(50):
        flags = fsm.feed(
            CheatSignals(
                liveness_score=0.95,
                deepfake_score=0.05,
                reid_similarity=0.95,
                audio_active=0.9,
                temporal_coherence_var=0.5,
                screen_replay_score=0.05,
            ),
            dt=0.1,
        )
        assert flags == []


def test_screen_replay_detected_immediately() -> None:
    fsm = CheatFSM()
    flags = fsm.feed(CheatSignals(screen_replay_score=0.85), dt=0.1)
    assert any(f.pattern == CheatPattern.SCREEN_REPLAY for f in flags)
