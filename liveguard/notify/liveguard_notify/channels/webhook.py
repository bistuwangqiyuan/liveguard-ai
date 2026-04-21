"""Webhook 通道 — 对客户自己的 URL 做 HMAC 签名 POST。"""

from __future__ import annotations

import time

import orjson

from .base import Channel, ChannelResult, NotificationJob


class WebhookChannel(Channel):
    name = "webhook"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        target = job.extras.get("url") or (job.targets[0] if job.targets else None)
        if not target:
            return ChannelResult(ok=False, channel=self.name, error="no webhook url")

        body = orjson.dumps(
            {
                "event": "lvg.alert",
                "alert_id": job.alert_id,
                "tenant_id": job.tenant_id,
                "severity": job.severity,
                "title": job.title,
                "summary": job.summary,
                "stream_id": job.stream_id,
                "host_id": job.host_id,
            }
        )
        secret = job.extras.get("secret", "")
        headers = {"content-type": "application/json"}
        if secret:
            headers["X-LiveGuard-Signature"] = self.sign_payload(secret, body)

        t0 = time.perf_counter()
        r = await self._client.post(target, content=body, headers=headers)
        elapsed = (time.perf_counter() - t0) * 1000.0
        if 200 <= r.status_code < 300:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, message_id=r.headers.get("x-request-id"))
        return ChannelResult(
            ok=False, channel=self.name, latency_ms=elapsed, error=f"http_{r.status_code}: {r.text[:200]}"
        )
