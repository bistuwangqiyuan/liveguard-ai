"""企业微信群机器人。"""

from __future__ import annotations

import time

from .base import Channel, ChannelResult, NotificationJob


class WeWorkChannel(Channel):
    name = "wework"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        url = job.extras.get("webhook_url")
        if not url:
            return ChannelResult(ok=False, channel=self.name, error="missing webhook_url")

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": (
                    f"# ⚠️ <font color='warning'>{job.severity}</font> · {job.title}\n"
                    f"> 流: `{job.stream_id}`\n"
                    f"> {job.summary}"
                )
            },
        }
        t0 = time.perf_counter()
        r = await self._client.post(url, json=payload)
        elapsed = (time.perf_counter() - t0) * 1000.0
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code == 200 and data.get("errcode") == 0:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, raw_response=data)
        return ChannelResult(
            ok=False, channel=self.name, latency_ms=elapsed,
            error=f"http_{r.status_code}_{data.get('errmsg', r.text[:120])}",
            raw_response=data,
        )
