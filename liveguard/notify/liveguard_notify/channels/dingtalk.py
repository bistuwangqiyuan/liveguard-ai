"""DingTalk 机器人 — Markdown 消息 + @手机号。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
import urllib.parse

from .base import Channel, ChannelResult, NotificationJob


class DingTalkChannel(Channel):
    name = "ding"

    async def _deliver(self, job: NotificationJob) -> ChannelResult:
        webhook = job.extras.get("webhook_url")
        secret = job.extras.get("secret")
        if not webhook:
            return ChannelResult(ok=False, channel=self.name, error="missing webhook_url")

        url = webhook
        if secret:
            ts = str(round(time.time() * 1000))
            string_to_sign = f"{ts}\n{secret}"
            hmac_code = hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            url = f"{webhook}&timestamp={ts}&sign={sign}"

        at_mobiles = job.targets or []
        severity_color = {"P0": "#D4380D", "P1": "#FA8C16", "P2": "#FAAD14", "INFO": "#52C41A"}.get(job.severity, "#1677FF")
        md = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"LiveGuard · {job.severity} · {job.title}",
                "text": (
                    f"# ⚠️ <font color='{severity_color}'>{job.severity}</font> · {job.title}\n\n"
                    f"**流:** {job.stream_id}\n\n"
                    f"{job.summary}\n\n"
                    f"{' '.join(f'@{m}' for m in at_mobiles)}"
                ),
            },
            "at": {"atMobiles": at_mobiles, "isAtAll": False},
        }

        t0 = time.perf_counter()
        r = await self._client.post(url, json=md)
        elapsed = (time.perf_counter() - t0) * 1000.0
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code == 200 and data.get("errcode") == 0:
            return ChannelResult(ok=True, channel=self.name, latency_ms=elapsed, raw_response=data)
        return ChannelResult(
            ok=False, channel=self.name, latency_ms=elapsed,
            error=f"http_{r.status_code}_errcode_{data.get('errcode')}:{data.get('errmsg', r.text[:120])}",
            raw_response=data,
        )
