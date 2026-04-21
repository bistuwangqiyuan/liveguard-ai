"""通知分发器 — 注入通道工厂，路由 NotificationJob → Channel.send。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .channels import CHANNELS, Channel, ChannelResult, NotificationJob


@dataclass(slots=True)
class DispatcherMetrics:
    total_sent: int = 0
    total_failed: int = 0
    by_channel_ok: dict[str, int] = None  # type: ignore[assignment]
    by_channel_fail: dict[str, int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.by_channel_ok = {}
        self.by_channel_fail = {}


class Dispatcher:
    def __init__(self, *, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient(timeout=8.0)
        self._cache: dict[str, Channel] = {}
        self.metrics = DispatcherMetrics()

    def _channel(self, name: str) -> Channel:
        if name not in self._cache:
            cls = CHANNELS.get(name)
            if cls is None:
                raise KeyError(f"unknown channel: {name}")
            self._cache[name] = cls(http_client=self._http)
        return self._cache[name]

    async def dispatch(self, job: NotificationJob) -> ChannelResult:
        ch = self._channel(job.channel)
        res = await ch.send(job)
        key = res.channel
        if res.ok:
            self.metrics.total_sent += 1
            self.metrics.by_channel_ok[key] = self.metrics.by_channel_ok.get(key, 0) + 1
        else:
            self.metrics.total_failed += 1
            self.metrics.by_channel_fail[key] = self.metrics.by_channel_fail.get(key, 0) + 1
        return res

    async def dispatch_many(self, jobs: list[NotificationJob]) -> list[ChannelResult]:
        results = []
        for j in jobs:
            try:
                results.append(await self.dispatch(j))
            except Exception as exc:  # noqa: BLE001
                results.append(ChannelResult(ok=False, channel=j.channel, error=str(exc)))
        return results

    async def aclose(self) -> None:
        await self._http.aclose()

    def snapshot(self) -> dict[str, Any]:
        return {
            "total_sent": self.metrics.total_sent,
            "total_failed": self.metrics.total_failed,
            "by_channel_ok": dict(self.metrics.by_channel_ok),
            "by_channel_fail": dict(self.metrics.by_channel_fail),
        }
