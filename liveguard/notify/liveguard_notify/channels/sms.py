"""SMS 通道 — 抽象适配阿里云/腾讯云短信。"""

from __future__ import annotations

import time
from typing import Any

from .base import Channel, ChannelResult, NotificationJob


class SmsChannel(Channel):
    """具体 SDK 由运行时配置 driver 决定（``aliyun`` / ``tencent`` / ``mock``）。

    所有驱动统一通过内部 HTTP endpoint 调用 — 避免把 SDK 硬编码在代码里。
    """

    name = "sms"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        driver = job.extras.get("driver", "mock")
        if driver == "mock":
            return ChannelResult(ok=True, channel=self.name, message_id=f"mock_{job.alert_id}", latency_ms=1.0)

        url = job.extras.get("api_url") or ""
        if not url:
            return ChannelResult(ok=False, channel=self.name, error="missing api_url")

        # 模板填槽：{severity}{title}{stream_id}
        payload: dict[str, Any] = {
            "driver": driver,
            "template_id": job.extras.get("template_id", "LVG_ALERT_001"),
            "sign_name": job.extras.get("sign_name", "守播LiveGuard"),
            "targets": job.targets,
            "params": {
                "severity": job.severity,
                "title": job.title[:40],
                "stream": job.stream_id,
            },
        }
        t0 = time.perf_counter()
        r = await self._client.post(url, json=payload, headers={
            "Authorization": f"Bearer {job.extras.get('api_token', '')}",
        })
        elapsed = (time.perf_counter() - t0) * 1000.0
        if 200 <= r.status_code < 300:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, message_id=r.json().get("id"))
        return ChannelResult(
            ok=False, channel=self.name, latency_ms=elapsed, error=f"http_{r.status_code}: {r.text[:120]}"
        )
