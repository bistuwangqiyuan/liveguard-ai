"""通道冒烟测试 — 使用 pytest-httpx 模拟远端。"""

from __future__ import annotations

import httpx
import pytest

from liveguard_notify.channels import (
    AppPushChannel,
    DingTalkChannel,
    FeishuChannel,
    NotificationJob,
    SmsChannel,
    VoiceChannel,
    WebhookChannel,
    WeWorkChannel,
)
from liveguard_notify.dispatcher import Dispatcher


def _job(channel: str, extras: dict | None = None) -> NotificationJob:
    return NotificationJob(
        alert_id="alt_abc",
        tenant_id="t_demo",
        severity="P1",
        channel=channel,
        title="测试告警",
        summary="状态: ON_DUTY → LONG_AWAY",
        stream_id="str_demo",
        host_id="h_alice",
        targets=["13800000000"],
        retry_policy={"max_retries": 1, "initial_backoff_s": 0.01},
        extras=extras or {},
    )


@pytest.mark.asyncio
async def test_webhook_signed_post(httpx_mock) -> None:
    httpx_mock.add_response(url="https://customer.example.com/webhook", method="POST", status_code=200)
    async with httpx.AsyncClient() as c:
        ch = WebhookChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("webhook", {"url": "https://customer.example.com/webhook", "secret": "s3cr3t"}))
    assert res.ok
    call = httpx_mock.get_request()
    assert call is not None
    assert call.headers.get("X-LiveGuard-Signature", "").startswith("sha256=")


@pytest.mark.asyncio
async def test_dingtalk_ok(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://oapi.dingtalk.com/robot/send?access_token=abc",
        method="POST",
        json={"errcode": 0, "errmsg": "ok"},
    )
    async with httpx.AsyncClient() as c:
        ch = DingTalkChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("ding", {"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=abc"}))
    assert res.ok


@pytest.mark.asyncio
async def test_wework_ok(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xyz",
        method="POST",
        json={"errcode": 0, "errmsg": "ok"},
    )
    async with httpx.AsyncClient() as c:
        ch = WeWorkChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("wework", {"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xyz"}))
    assert res.ok


@pytest.mark.asyncio
async def test_feishu_ok(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://open.feishu.cn/open-apis/bot/v2/hook/abcdef",
        method="POST",
        json={"code": 0, "msg": "ok"},
    )
    async with httpx.AsyncClient() as c:
        ch = FeishuChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("feishu", {"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/abcdef"}))
    assert res.ok


@pytest.mark.asyncio
async def test_sms_mock_driver() -> None:
    async with httpx.AsyncClient() as c:
        ch = SmsChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("sms", {"driver": "mock"}))
    assert res.ok
    assert res.message_id is not None


@pytest.mark.asyncio
async def test_voice_mock_driver() -> None:
    async with httpx.AsyncClient() as c:
        ch = VoiceChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("voice", {"driver": "mock"}))
    assert res.ok


@pytest.mark.asyncio
async def test_push_mock_driver() -> None:
    async with httpx.AsyncClient() as c:
        ch = AppPushChannel(http_client=c, max_retries=1)
        res = await ch.send(_job("push", {"driver": "mock"}))
    assert res.ok


@pytest.mark.asyncio
async def test_dispatcher_routes_and_counts(httpx_mock) -> None:
    httpx_mock.add_response(url="https://example.com/w", method="POST", status_code=200)
    d = Dispatcher()
    await d.dispatch(_job("webhook", {"url": "https://example.com/w"}))
    await d.dispatch(_job("sms", {"driver": "mock"}))
    snap = d.snapshot()
    assert snap["total_sent"] == 2
    assert snap["by_channel_ok"]["webhook"] == 1
    assert snap["by_channel_ok"]["sms"] == 1
    await d.aclose()
