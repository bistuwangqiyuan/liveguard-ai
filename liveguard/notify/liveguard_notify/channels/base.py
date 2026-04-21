"""通道基类 + 共同 DTO。"""

from __future__ import annotations

import hashlib
import hmac
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential


@dataclass(slots=True)
class NotificationJob:
    alert_id: str
    tenant_id: str
    severity: str
    channel: str
    title: str
    summary: str
    stream_id: str
    host_id: str | None
    targets: list[str] = field(default_factory=list)
    retry_policy: dict[str, int] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChannelResult:
    ok: bool
    channel: str
    message_id: str | None = None
    latency_ms: float = 0.0
    error: str | None = None
    attempts: int = 1
    raw_response: dict[str, Any] = field(default_factory=dict)


class Channel(ABC):
    name: str = "base"

    def __init__(self, *, http_client: httpx.AsyncClient | None = None,
                 max_retries: int = 3, initial_backoff_s: float = 1.0) -> None:
        self._client = http_client or httpx.AsyncClient(timeout=8.0)
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff_s

    @abstractmethod
    async def _deliver(self, job: NotificationJob) -> ChannelResult: ...

    async def send(self, job: NotificationJob) -> ChannelResult:
        retries = job.retry_policy.get("max_retries", self._max_retries)
        backoff = job.retry_policy.get("initial_backoff_s", self._initial_backoff)
        attempt = 0
        last_exc: Exception | None = None
        async for attempt_ in AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential(multiplier=backoff, max=30.0),
            reraise=True,
        ):
            with attempt_:
                attempt = attempt_.retry_state.attempt_number
                try:
                    res = await self._deliver(job)
                    res.attempts = attempt
                    if res.ok:
                        return res
                    raise RuntimeError(res.error or "send_failed")
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    raise
        return ChannelResult(
            ok=False, channel=self.name, attempts=attempt, error=str(last_exc) if last_exc else "unknown"
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def sign_payload(secret: str, body: bytes) -> str:
        return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
