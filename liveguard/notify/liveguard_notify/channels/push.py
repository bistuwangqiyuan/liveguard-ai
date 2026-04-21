"""App Push —— FCM / APNs / 个推/友盟 抽象。"""

from __future__ import annotations

import time

from .base import Channel, ChannelResult, NotificationJob


class AppPushChannel(Channel):
    name = "push"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        driver = job.extras.get("driver", "mock")
        if driver == "mock":
            return ChannelResult(ok=True, channel=self.name, message_id=f"push_{job.alert_id}", latency_ms=1.0)

        url = job.extras.get("api_url", "")
        if not url:
            return ChannelResult(ok=False, channel=self.name, error="missing api_url")

        payload = {
            "driver": driver,
            "devices": job.targets,
            "title": f"[{job.severity}] {job.title}",
            "body": job.summary,
            "data": {"alert_id": job.alert_id, "stream_id": job.stream_id},
            "collapse_key": job.alert_id,
            "priority": "high" if job.severity in ("P0", "P1") else "normal",
        }
        t0 = time.perf_counter()
        r = await self._client.post(url, json=payload, headers={
            "Authorization": f"Bearer {job.extras.get('api_token', '')}",
        })
        elapsed = (time.perf_counter() - t0) * 1000.0
        if 200 <= r.status_code < 300:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed)
        return ChannelResult(ok=False, channel=self.name, latency_ms=elapsed,
                             error=f"http_{r.status_code}: {r.text[:120]}")
