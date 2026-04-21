"""
liveguard_backend.services.notify_dispatcher
============================================

通道分发的 *编排* — 真正发送由 ``notify/`` 微服务完成。这里只：

1. 根据租户策略（severity × channel）选择需要推送的通道。
2. 把任务丢进 ``notify.jobs.v1`` 主题，由 Notify Service 消费。
"""

from __future__ import annotations

from typing import Any

from ..domain.enums import Severity
from ..domain.models import Alert
from ..infra.bus import EventBus

DEFAULT_CHANNEL_MATRIX = {
    Severity.INFO: ("webhook",),
    Severity.P2: ("webhook", "ding"),
    Severity.P1: ("webhook", "ding", "wework", "sms"),
    Severity.P0: ("webhook", "ding", "wework", "sms", "voice"),
}


class NotificationDispatcher:
    def __init__(self, bus: EventBus, channel_matrix: dict[Severity, tuple[str, ...]] | None = None) -> None:
        self._bus = bus
        self._matrix = channel_matrix or DEFAULT_CHANNEL_MATRIX

    async def dispatch(self, alert: Alert, *, target_users: list[str] | None = None) -> list[dict[str, Any]]:
        channels = self._matrix.get(alert.severity, ("webhook",))
        jobs = []
        for ch in channels:
            job = {
                "alert_id": alert.id,
                "tenant_id": alert.tenant_id,
                "severity": alert.severity.value,
                "channel": ch,
                "title": alert.title,
                "summary": alert.summary,
                "stream_id": alert.stream_id,
                "host_id": alert.host_id,
                "targets": target_users or [],
                "retry_policy": _retry_policy_for(alert.severity),
            }
            await self._bus.publish("notify.jobs.v1", job, key=alert.tenant_id)
            jobs.append(job)
        return jobs


def _retry_policy_for(sev: Severity) -> dict[str, int]:
    if sev == Severity.P0:
        return {"max_retries": 5, "initial_backoff_s": 1, "max_backoff_s": 30}
    if sev == Severity.P1:
        return {"max_retries": 3, "initial_backoff_s": 2, "max_backoff_s": 60}
    return {"max_retries": 2, "initial_backoff_s": 5, "max_backoff_s": 120}
