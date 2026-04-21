"""
liveguard_backend.services.alert_manager
========================================

告警编排：聚合事件 → 告警生命周期（open → acked → resolved）。

策略（``Requirements §5 Alerting SLO``）：
* 同一 stream_id + severity 在 5 分钟去重：同一事件序列合并为一个 open 告警。
* P0 即刻创建并推送 Notify Service；P1 创建但允许用户批量确认。
* INFO 仅写事件不创建告警。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable
from uuid import uuid4

from ..domain.enums import AlertState, Severity
from ..domain.models import Alert, EventRecord
from ..infra.bus import EventBus
from ..infra.metrics import ALERTS_TOTAL

AlertPublisher = Callable[[Alert], Awaitable[None]]


class AlertManager:
    DEDUP_WINDOW_S = 300

    def __init__(self, bus: EventBus, publisher: AlertPublisher | None = None) -> None:
        self._bus = bus
        self._publisher = publisher
        self._recent: dict[tuple[str, str, str], Alert] = {}

    async def on_event(self, ev: EventRecord) -> Alert | None:
        if ev.severity not in (Severity.P1, Severity.P0):
            return None

        key = (ev.tenant_id, ev.stream_id, ev.severity.value)
        cached = self._recent.get(key)
        now = datetime.now(UTC)
        if cached and (now - cached.first_seen_at) < timedelta(seconds=self.DEDUP_WINDOW_S):
            cached.event_ids.append(ev.id)
            return cached

        alert = Alert(
            id=f"alt_{uuid4().hex[:24]}",
            tenant_id=ev.tenant_id,
            stream_id=ev.stream_id,
            host_id=ev.host_id,
            severity=ev.severity,
            state=AlertState.OPEN,
            event_ids=[ev.id],
            title=_title_for(ev),
            summary=_summary_for(ev),
            first_seen_at=now,
        )
        self._recent[key] = alert
        ALERTS_TOTAL.labels(tenant=ev.tenant_id, severity=ev.severity.value, state="open").inc()

        await self._bus.publish(
            "alerts.v1",
            {
                "specversion": "1.0",
                "id": alert.id,
                "type": f"lvg.alert.{ev.severity.value.lower()}.v1",
                "source": f"lvg://tenant/{ev.tenant_id}/stream/{ev.stream_id}",
                "subject": f"alert/{alert.id}",
                "time": now.isoformat(timespec="milliseconds"),
                "data": alert.model_dump(mode="json"),
            },
            key=alert.stream_id,
        )
        if self._publisher:
            await self._publisher(alert)
        return alert


def _title_for(ev: EventRecord) -> str:
    if ev.to_state == "LONG_AWAY":
        return f"主播离岗 ≥ 60s · {ev.stream_id}"
    if ev.to_state == "ALERT_ESCALATED":
        return f"P0 紧急 · 主播离岗 > 3 分钟 · {ev.stream_id}"
    if ev.event_type.startswith("lvg.cheat."):
        return f"反作弊告警 · {ev.event_type.removeprefix('lvg.cheat.').removesuffix('.v1').upper()} · {ev.stream_id}"
    return f"事件 · {ev.event_type} · {ev.stream_id}"


def _summary_for(ev: EventRecord) -> str:
    parts = [
        f"状态: {ev.from_state} → {ev.to_state}",
        f"融合得分: {ev.fusion_score:.3f}",
        f"累计离开: {ev.duration_offline_s:.1f}s",
    ]
    return " ｜ ".join(parts)
