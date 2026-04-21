"""
liveguard_algo.pipeline
=======================

多模态在线推理流水线 — 实现 ``Design §5.2`` 数据流：

1. 接收一帧视频 (BGR) + 一段对应的 PCM 音频。
2. 调用 face / person / liveness / action / vad / speaker 各子系统。
3. 把 6 路 score 转成 :class:`SignalFrame`，喂给 :class:`StreamFSM` 与
   :class:`CheatFSM`。
4. 返回结构化的 :class:`PipelineFrameResult`，外层 worker 负责往 Kafka 写。

流水线是同步的，便于单元测试；生产环境用 asyncio + ProcessPoolExecutor 并行
跑各子模型。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .action import ActionScorerMock, MoveNetMock
from .audio import SpeakerProfileGallery, SpeakerVerifierMock, VadProcessorMock
from .face import FaceDetectorMock, FaceEmbedderMock
from .fusion import (
    CheatFlag,
    CheatFSM,
    CheatSignals,
    SignalFrame,
    StateTransitionEvent,
    StreamFSM,
)
from .liveness import LivenessScorerMock
from .person import PersonDetectorMock, ReIDExtractorMock, ReIDGallery


@dataclass(slots=True)
class PipelineFrameResult:
    timestamp_s: float
    state_event: Optional[StateTransitionEvent]
    cheat_flags: list[CheatFlag]
    signals: SignalFrame
    fusion_score: float
    latency_ms: float
    debug: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineConfig:
    enroll_after_n_frames: int = 25
    require_liveness_for_on_duty: bool = True
    edge_only_audio: bool = False  # 隐私模式：不上传声纹


class LiveGuardPipeline:
    """单流（single livestream）多模态实时分析器。

    组件全为可注入；测试时可以替换为 mock，生产时注入 ONNX / TensorRT 实现。
    """

    def __init__(
        self,
        stream_id: str,
        host_id: str = "host-default",
        *,
        face_detector: FaceDetectorMock | None = None,
        face_embedder: FaceEmbedderMock | None = None,
        person_detector: PersonDetectorMock | None = None,
        reid_extractor: ReIDExtractorMock | None = None,
        reid_gallery: ReIDGallery | None = None,
        liveness: LivenessScorerMock | None = None,
        movenet: MoveNetMock | None = None,
        action_scorer: ActionScorerMock | None = None,
        vad: VadProcessorMock | None = None,
        speaker: SpeakerVerifierMock | None = None,
        speaker_gallery: SpeakerProfileGallery | None = None,
        stream_fsm: StreamFSM | None = None,
        cheat_fsm: CheatFSM | None = None,
        config: PipelineConfig | None = None,
    ) -> None:
        self.stream_id = stream_id
        self.host_id = host_id
        self.cfg = config or PipelineConfig()

        self.face_detector = face_detector or FaceDetectorMock()
        self.face_embedder = face_embedder or FaceEmbedderMock()
        self.person_detector = person_detector or PersonDetectorMock()
        self.reid_extractor = reid_extractor or ReIDExtractorMock()
        self.reid_gallery = reid_gallery or ReIDGallery()
        self.liveness = liveness or LivenessScorerMock()
        self.movenet = movenet or MoveNetMock()
        self.action_scorer = action_scorer or ActionScorerMock()
        self.vad = vad or VadProcessorMock()
        self.speaker = speaker or SpeakerVerifierMock()
        self.speaker_gallery = speaker_gallery or SpeakerProfileGallery()

        self.stream_fsm = stream_fsm or StreamFSM(stream_id=stream_id)
        self.cheat_fsm = cheat_fsm or CheatFSM(stream_id=stream_id)

        self._frame_id = 0
        self._enrolled = False

    def process(self, frame_bgr: np.ndarray | None, pcm: np.ndarray | None,
                dt: float, timestamp_s: float | None = None) -> PipelineFrameResult:
        t0 = time.perf_counter()
        self._frame_id += 1
        ts = timestamp_s if timestamp_s is not None else (t0)

        face_frame = self.face_detector.detect(frame_bgr, self._frame_id, ts) if frame_bgr is not None else None
        person_frame = self.person_detector.detect(frame_bgr, self._frame_id, ts) if frame_bgr is not None else None

        face_score = float(face_frame.primary.score) if face_frame and face_frame.primary else 0.0
        person_score = float(person_frame.primary.score) if person_frame and person_frame.primary else 0.0

        # Re-ID（仅当有 person + face 时）
        reid_score = 0.0
        face_emb: np.ndarray | None = None
        if frame_bgr is not None and face_frame and face_frame.primary:
            crop = self._crop(frame_bgr, face_frame.primary.x1, face_frame.primary.y1,
                              face_frame.primary.x2, face_frame.primary.y2)
            face_emb = self.face_embedder.embed(crop)
            if not self._enrolled and self._frame_id >= self.cfg.enroll_after_n_frames:
                self.reid_gallery.enroll(self.host_id, face_emb)
                self._enrolled = True
                reid_score = 1.0
            elif self._enrolled:
                _, reid_score = self.reid_gallery.match(face_emb)
                self.reid_gallery.update(self.host_id, face_emb)
                reid_score = float(np.clip(reid_score, 0.0, 1.0))

        # Liveness
        live_res = None
        liveness_score = 0.0
        deepfake = 0.0
        if frame_bgr is not None and face_frame and face_frame.primary:
            roi = self._crop(frame_bgr, face_frame.primary.x1, face_frame.primary.y1,
                             face_frame.primary.x2, face_frame.primary.y2)
            live_res = self.liveness.feed(roi)
            liveness_score = live_res.liveness_score
            deepfake = live_res.deepfake_score

        # Action
        action_score = 0.0
        if frame_bgr is not None:
            kps = self.movenet.estimate(frame_bgr)
            action_res = self.action_scorer.feed(kps)
            action_score = action_res.activity

        # Audio
        audio_score = 0.0
        spk_score = 1.0
        if pcm is not None and pcm.size > 0 and not self.cfg.edge_only_audio:
            vad_frame = self.vad.process(pcm)
            audio_score = vad_frame.is_voice
            if vad_frame.is_voice >= 0.5:
                spk_emb = self.speaker.embed(pcm)
                if self.host_id not in self.speaker_gallery.keys():
                    self.speaker_gallery.enroll(self.host_id, spk_emb)
                else:
                    _, spk_score = self.speaker_gallery.verify(self.host_id, spk_emb)

        signals = SignalFrame(
            face=face_score,
            person=person_score,
            reid=reid_score,
            liveness=liveness_score,
            action=action_score,
            audio=audio_score,
        )
        evt = self.stream_fsm.feed(signals, dt)

        cheat_signals = CheatSignals(
            liveness_score=liveness_score,
            deepfake_score=deepfake,
            reid_similarity=reid_score if self._enrolled else 1.0,
            audio_active=audio_score,
            temporal_coherence_var=getattr(live_res, "temporal_var", 0.5) / 25.0 if live_res else 0.5,
            screen_replay_score=0.0,
        )
        cheat_flags = self.cheat_fsm.feed(cheat_signals, dt)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return PipelineFrameResult(
            timestamp_s=ts,
            state_event=evt,
            cheat_flags=cheat_flags,
            signals=signals,
            fusion_score=self.stream_fsm.last_fusion_score,
            latency_ms=latency_ms,
            debug={
                "deepfake": deepfake,
                "spk_score": spk_score,
                "reid_score": reid_score,
                "frame_id": float(self._frame_id),
            },
        )

    @staticmethod
    def _crop(frame: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> np.ndarray:
        h, w = frame.shape[:2]
        xi1, yi1 = max(0, int(x1)), max(0, int(y1))
        xi2, yi2 = min(w, int(x2)), min(h, int(y2))
        if xi2 <= xi1 or yi2 <= yi1:
            return np.zeros((1, 1, 3), dtype=frame.dtype)
        return frame[yi1:yi2, xi1:xi2]
