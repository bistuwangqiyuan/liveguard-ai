"""端到端测试：上行信号 → FSM → 事件 → 告警 → 通知 job。"""

from __future__ import annotations

import pytest

from liveguard_backend.domain.enums import Severity
from liveguard_backend.domain.models import EventRecord, SignalIngest
from liveguard_backend.infra.bus import InMemoryEventBus
from liveguard_backend.services import (
    AlertManager,
    IngestService,
    NotificationDispatcher,
    StreamFSMStore,
)


def _strong() -> dict:
    return dict(face=0.95, person=0.92, reid=0.9, liveness=0.93, action=0.5, audio=0.8)


def _weak() -> dict:
    return dict(face=0.0, person=0.0, reid=0.0, liveness=0.0, action=0.0, audio=0.0)


@pytest.mark.asyncio
async def test_ingest_produces_state_transition_and_alert_for_p1() -> None:
    bus = InMemoryEventBus()
    await bus.start()
    store = StreamFSMStore()
    svc = IngestService(store, bus)
    dispatcher = NotificationDispatcher(bus)
    alert_mgr = AlertManager(bus, publisher=dispatcher.dispatch)

    # 先 ON_DUTY
    await svc.ingest(
        SignalIngest(stream_id="s1", ts_ms=0, **_strong()),
        tenant_id="t_demo",
    )
    # 再持续 weak 导致 BRIEF/LONG_AWAY
    alerts_created = []
    ts = 200
    for _ in range(400):  # 共 80s 的 weak 信号
        result = await svc.ingest(
            SignalIngest(stream_id="s1", ts_ms=ts, **_weak()),
            tenant_id="t_demo",
        )
        ts += 200
        for ev_dict in result["events_emitted"]:
            alert = await alert_mgr.on_event(EventRecord.model_validate(ev_dict))
            if alert:
                alerts_created.append(alert)

    severities = {a.severity for a in alerts_created}
    assert Severity.P1 in severities

    # Notify 任务应进入 in-memory bus
    notify_topics = [t for t, _ in bus.published if t == "notify.jobs.v1"]
    assert len(notify_topics) > 0


@pytest.mark.asyncio
async def test_ingest_dedups_repeat_alerts() -> None:
    bus = InMemoryEventBus()
    await bus.start()
    store = StreamFSMStore()
    svc = IngestService(store, bus)
    alert_mgr = AlertManager(bus)

    await svc.ingest(SignalIngest(stream_id="s2", ts_ms=0, **_strong()), tenant_id="t2")
    ts = 200
    all_events: list[EventRecord] = []
    for _ in range(500):
        result = await svc.ingest(SignalIngest(stream_id="s2", ts_ms=ts, **_weak()), tenant_id="t2")
        ts += 200
        for ev in result["events_emitted"]:
            all_events.append(EventRecord.model_validate(ev))

    seen_alerts: list = []
    for ev in all_events:
        a = await alert_mgr.on_event(ev)
        if a is not None:
            seen_alerts.append(a)
    # 去重后同一 severity 应只开一个 open alert
    by_sev: dict = {}
    for a in seen_alerts:
        by_sev.setdefault(a.severity, []).append(a)
    for _, alerts in by_sev.items():
        ids = {a.id for a in alerts}
        assert len(ids) == 1
