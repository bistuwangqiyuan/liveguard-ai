"""语音电话通道 — 对 P0 强制拨打（TTS）。"""

from __future__ import annotations

import time

from .base import Channel, ChannelResult, NotificationJob


class VoiceChannel(Channel):
    name = "voice"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        driver = job.extras.get("driver", "mock")
        if driver == "mock":
            return ChannelResult(ok=True, channel=self.name, message_id=f"call_{job.alert_id}", latency_ms=1.0)

        url = job.extras.get("api_url", "")
        if not url:
            return ChannelResult(ok=False, channel=self.name, error="missing api_url")

        payload = {
            "driver": driver,
            "call_flow_id": job.extras.get("call_flow_id", "LVG_P0_V1"),
            "targets": job.targets,
            "tts_text": f"守播 L I V E  G U A R D 紧急告警。{job.title}。严重级别{job.severity}。请立即处理。",
        }
        t0 = time.perf_counter()
        r = await self._client.post(url, json=payload, headers={
            "Authorization": f"Bearer {job.extras.get('api_token', '')}",
        })
        elapsed = (time.perf_counter() - t0) * 1000.0
        if 200 <= r.status_code < 300:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, message_id=r.json().get("call_id"))
        return ChannelResult(ok=False, channel=self.name, latency_ms=elapsed,
                             error=f"http_{r.status_code}: {r.text[:120]}")
