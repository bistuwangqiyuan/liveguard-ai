"""飞书自定义机器人 — interactive card。"""

from __future__ import annotations

import time

from .base import Channel, ChannelResult, NotificationJob


class FeishuChannel(Channel):
    name = "feishu"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        url = job.extras.get("webhook_url")
        if not url:
            return ChannelResult(ok=False, channel=self.name, error="missing webhook_url")
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"LiveGuard · {job.severity} · {job.title}"},
                    "template": {"P0": "red", "P1": "orange", "P2": "yellow"}.get(job.severity, "blue"),
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"**流:** {job.stream_id}\n{job.summary}"}},
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "查看详情"},
                                "type": "primary",
                                "url": job.extras.get("console_url", f"https://console.liveguard.ai/streams/{job.stream_id}"),
                            }
                        ],
                    },
                ],
            },
        }
        t0 = time.perf_counter()
        r = await self._client.post(url, json=payload)
        elapsed = (time.perf_counter() - t0) * 1000.0
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code == 200 and data.get("code", 0) == 0:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, raw_response=data)
        return ChannelResult(
            ok=False, channel=self.name, latency_ms=elapsed,
            error=f"http_{r.status_code}_{data.get('msg', r.text[:120])}",
            raw_response=data,
        )
