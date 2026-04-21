"""API 冒烟测试（httpx.ASGITransport + 无依赖 sqlite 内存库）。"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from liveguard_backend.db import get_engine, init_db
from liveguard_backend.domain.enums import Role
from liveguard_backend.domain.models import Tenant, User
from liveguard_backend.main import app
from liveguard_backend.security.auth import PasswordHasher, create_access_token


@pytest.fixture()
async def client():
    # 触发 lifespan 启动
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        # FastAPI lifespan 需手动触发
        async with app.router.lifespan_context(app):
            yield c

    # cleanup — 清理 engine 避免跨测试串
    engine = get_engine()
    await engine.dispose()


@pytest.mark.asyncio
async def test_healthz(client) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_metrics_route(client) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "lvg_" in r.text


@pytest.mark.asyncio
async def test_auth_required_for_streams(client) -> None:
    r = await client.get("/v1/streams")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_ingest_flow_happy_path(client, monkeypatch) -> None:
    # 手动塞入 tenant + token
    await init_db()
    from sqlalchemy.ext.asyncio import AsyncSession

    from liveguard_backend.db import get_sessionmaker
    from liveguard_backend.db.repositories import TenantRepo, UserRepo

    sm = get_sessionmaker()
    async with sm() as s:
        sess: AsyncSession = s
        await TenantRepo(sess).create(Tenant(id="t_demo", name="Demo"))
        await UserRepo(sess).create(
            User(
                id="u_demo",
                tenant_id="t_demo",
                email="alice@demo.ai",
                hashed_password=PasswordHasher.hash("SecurePass123!"),
                role=Role.ADMIN,
                display_name="Alice",
            )
        )
        await sess.commit()

    tok = create_access_token(
        subject="u_demo", tenant_id="t_demo", role=Role.ADMIN,
        scopes=("streams:read", "streams:write", "events:read"),
    )
    headers = {"Authorization": f"Bearer {tok}"}
    r = await client.post(
        "/v1/streams",
        json={"platform": "douyin", "rtmp_url": "rtmp://example/live/abc"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    stream_id = r.json()["id"]

    # ingest a strong signal → expect state transition
    r = await client.post(
        "/v1/ingest/signals",
        json={
            "stream_id": stream_id,
            "ts_ms": 0,
            "face": 0.95, "person": 0.92, "reid": 0.9,
            "liveness": 0.93, "action": 0.5, "audio": 0.7,
        },
        headers=headers,
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["state"] == "ON_DUTY"
    assert body["fusion_score"] >= 0.65
    assert body["state_event"] is not None
    assert body["state_event"]["to"] == "ON_DUTY"
