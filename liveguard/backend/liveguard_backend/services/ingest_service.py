"""
liveguard_backend.services.ingest_service
=========================================

边缘上行 → 领域事件 流水线。

数据流：

.. code-block:: text

    SignalIngest (POST /v1/ingest/signals)
        └─▶ StreamFSMStore.feed
                └─▶ StateTransitionEvent? + CheatFlag[]
                        ├─▶ EventRepo.add (Postgres 审计)
                        ├─▶ EventBus.publish (Kafka streams.events.v1)
                        └─▶ AlertManager.maybe_create_alert
"""

from __future__ import annotations

from asyncio import Lock
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from liveguard_algo import (
    CheatFSM,
    CheatFlag,
    CheatSignals,
    FSMConfig,
    SignalFrame,
    StateTransitionEvent,
    StreamFSM,
    StreamState,
)
from liveguard_algo.fusion.explainer import to_cloudevent

from ..domain.enums import Severity
from ..domain.models import EventRecord, SignalIngest
from ..infra.bus import EventBus
from ..infra.metrics import ACTIVE_STREAMS, EVENTS_TOTAL, INGEST_TOTAL


@dataclass(slots=True)
class _FSMPair:
    stream_fsm: StreamFSM
    cheat_fsm: CheatFSM
    last_ts_ms: int = 0
    tenant_id: str = ""
    host_id: str | None = None
    platform: str = "unknown"


class StreamFSMStore:
    """每个活跃流一个 (StreamFSM, CheatFSM)；进程内单例。

    生产环境可换成 Redis-backed 或 stateful Kubernetes actor（每流 1 pod），
    此处用内存实现便于本地 demo 与单元测试。
    """

    def __init__(self, fsm_config: FSMConfig | None = None) -> None:
        self._lock = Lock()
        self._items: dict[str, _FSMPair] = {}
        self._cfg = fsm_config or FSMConfig()

    async def get_or_create(
        self, stream_id: str, *, tenant_id: str, host_id: str | None = None, platform: str = "unknown"
    ) -> _FSMPair:
        async with self._lock:
            item = self._items.get(stream_id)
            if item is None:
                item = _FSMPair(
                    stream_fsm=StreamFSM(stream_id=stream_id, config=self._cfg),
                    cheat_fsm=CheatFSM(stream_id=stream_id),
                    tenant_id=tenant_id,
                    host_id=host_id,
                    platform=platform,
                )
                self._items[stream_id] = item
            return item

    async def drop(self, stream_id: str) -> None:
        async with self._lock:
            self._items.pop(stream_id, None)

    async def stats(self) -> dict[str, int]:
        async with self._lock:
            return {"active_streams": len(self._items)}


class IngestService:
    """把 edge 上行的 ``SignalIngest`` 喂给 FSM 并产生领域事件。"""

    def __init__(self, store: StreamFSMStore, bus: EventBus) -> None:
        self.store = store
        self.bus = bus

    async def ingest(
        self, signal: SignalIngest, *, tenant_id: str, host_id: str | None = None, platform: str = "unknown"
    ) -> dict[str, Any]:
        pair = await self.store.get_or_create(
            signal.stream_id, tenant_id=tenant_id, host_id=host_id, platform=platform
        )
        dt = _compute_dt(pair, signal)

        sf = SignalFrame(
            face=signal.face,
            person=signal.person,
            reid=signal.reid,
            liveness=signal.liveness,
            action=signal.action,
            audio=signal.audio,
        )
        evt: StateTransitionEvent | None = pair.stream_fsm.feed(sf, dt=dt)
        flags: list[CheatFlag] = pair.cheat_fsm.feed(
            CheatSignals(
                liveness_score=signal.liveness,
                deepfake_score=signal.deepfake,
                reid_similarity=signal.reid_similarity,
                audio_active=signal.audio,
                temporal_coherence_var=signal.temporal_var,
                screen_replay_score=signal.screen_replay,
            ),
            dt=dt,
        )

        out_events: list[EventRecord] = []
        ce_envelopes: list[dict[str, Any]] = []

        if evt is not None:
            rec = _to_event_record(evt, tenant_id=tenant_id, stream_id=signal.stream_id, host_id=host_id)
            out_events.append(rec)
            ce = to_cloudevent(evt, tenant_id=tenant_id, host_id=host_id, platform=platform)
            ce_envelopes.append(ce)
            EVENTS_TOTAL.labels(tenant=tenant_id, severity=rec.severity.value).inc()

        for f in flags:
            fake_ev = _cheat_as_event(f, stream_id=signal.stream_id, tenant_id=tenant_id, host_id=host_id)
            out_events.append(fake_ev)
            ce_envelopes.append(_cheat_cloudevent(f, stream_id=signal.stream_id, tenant_id=tenant_id))
            EVENTS_TOTAL.labels(tenant=tenant_id, severity=f.severity).inc()

        INGEST_TOTAL.labels(tenant=tenant_id, status="ok").inc()
        ACTIVE_STREAMS.labels(tenant=tenant_id).set(len((await self.store.stats()).values()))

        # 异步发布到事件总线（Kafka or in-memory）
        for env in ce_envelopes:
            await self.bus.publish("streams.events.v1", env, key=signal.stream_id)

        return {
            "stream_id": signal.stream_id,
            "state": pair.stream_fsm.state.value,
            "fusion_score": round(pair.stream_fsm.last_fusion_score, 4),
            "offline_seconds": pair.stream_fsm.offline_seconds,
            "state_event": _simple(evt) if evt else None,
            "cheat_flags": [{"pattern": f.pattern.value, "confidence": f.confidence, "severity": f.severity} for f in flags],
            "events_emitted": [e.model_dump(mode="json") for e in out_events],
        }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _compute_dt(pair: _FSMPair, signal: SignalIngest) -> float:
    if pair.last_ts_ms == 0 or signal.ts_ms <= pair.last_ts_ms:
        dt = 0.2  # 默认 200 ms 步长
    else:
        dt = max(0.02, min(5.0, (signal.ts_ms - pair.last_ts_ms) / 1000.0))
    pair.last_ts_ms = signal.ts_ms
    return dt


def _simple(evt: StateTransitionEvent) -> dict[str, Any]:
    return {
        "event_id": evt.event_id,
        "from": evt.from_state.value,
        "to": evt.to_state.value,
        "fusion_score": evt.fusion_score,
        "severity": evt.severity,
        "timer_offline_s": evt.timer_offline_s,
    }


def _to_event_record(
    evt: StateTransitionEvent, *, tenant_id: str, stream_id: str, host_id: str | None
) -> EventRecord:
    names = ("face", "person", "reid", "liveness", "action", "audio")
    return EventRecord(
        id=evt.event_id,
        tenant_id=tenant_id,
        stream_id=stream_id,
        host_id=host_id,
        event_type=_event_type(evt),
        from_state=evt.from_state.value,
        to_state=evt.to_state.value,
        fusion_score=evt.fusion_score,
        severity=Severity(evt.severity),
        signal_breakdown={k: getattr(evt.signals, k) for k in names},
        weights_used={k: v for k, v in zip(names, evt.weights_used)},
        duration_offline_s=evt.timer_offline_s,
    )


def _event_type(evt: StateTransitionEvent) -> str:
    if evt.to_state == StreamState.LONG_AWAY:
        return "lvg.alert.host_offline.v1"
    if evt.to_state == StreamState.ALERT_ESCALATED:
        return "lvg.alert.host_offline_escalated.v1"
    if evt.to_state == StreamState.ON_DUTY:
        return "lvg.host.online.v1"
    if evt.to_state == StreamState.BRIEF_AWAY:
        return "lvg.host.offline.v1"
    return "lvg.stream.state_changed.v1"


def _cheat_as_event(
    f: CheatFlag, *, stream_id: str, tenant_id: str, host_id: str | None
) -> EventRecord:
    return EventRecord(
        id=f"evt_{uuid4().hex[:24]}",
        tenant_id=tenant_id,
        stream_id=stream_id,
        host_id=host_id,
        event_type=f"lvg.cheat.{f.pattern.value.lower()}.v1",
        from_state="ANY",
        to_state="CHEAT_FLAGGED",
        fusion_score=f.confidence,
        severity=Severity(f.severity),
        extras={"evidence": f.evidence, "pattern": f.pattern.value},
    )


def _cheat_cloudevent(f: CheatFlag, *, stream_id: str, tenant_id: str) -> dict[str, Any]:
    import datetime as _dt
    return {
        "specversion": "1.0",
        "id": f"evt_cheat_{uuid4().hex[:20]}",
        "type": f"lvg.cheat.{f.pattern.value.lower()}.v1",
        "source": f"lvg://tenant/{tenant_id}/stream/{stream_id}",
        "subject": f"stream/{stream_id}",
        "time": _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds"),
        "datacontenttype": "application/json",
        "data": {
            "tenant_id": tenant_id,
            "stream_id": stream_id,
            "pattern": f.pattern.value,
            "confidence": f.confidence,
            "severity": f.severity,
            "evidence": f.evidence,
        },
    }
