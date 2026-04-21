"""
liveguard 种子数据
==================

为本地 demo / E2E 测试准备一个 "拎包入住" 的数据集：
* 1 个 demo 租户（t_demo）
* 3 个用户：owner、operator、viewer
* 3 位主播（Alice、Bob、Cathy）
* 3 条直播流（抖音、快手、自定义 RTMP）
* 近一天的演示事件若干

执行：``python -m liveguard_backend.scripts.seed``
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from liveguard_backend.db import get_sessionmaker, init_db
from liveguard_backend.db.repositories import (
    AlertRepo,
    EventRepo,
    HostRepo,
    StreamRepo,
    TenantRepo,
    UserRepo,
)
from liveguard_backend.domain.enums import AlertState, Role, Severity, StreamStatus
from liveguard_backend.domain.models import (
    Alert,
    EventRecord,
    Host,
    Stream,
    Tenant,
    User,
)
from liveguard_backend.security.auth import PasswordHasher


async def seed() -> None:
    await init_db()
    sm = get_sessionmaker()

    async with sm() as s:
        t_repo = TenantRepo(s)
        u_repo = UserRepo(s)
        h_repo = HostRepo(s)
        str_repo = StreamRepo(s)
        ev_repo = EventRepo(s)
        al_repo = AlertRepo(s)

        if await t_repo.get("t_demo") is None:
            await t_repo.create(
                Tenant(id="t_demo", name="DemoShop 旗舰店", plan="pro", region="cn-east-1")
            )
        users = [
            ("u_owner", "owner@demo.ai", "Owner", Role.OWNER, "Demo@0425!"),
            ("u_ops", "ops@demo.ai", "Ops", Role.OPERATOR, "Demo@0425!"),
            ("u_view", "viewer@demo.ai", "Viewer", Role.VIEWER, "Demo@0425!"),
        ]
        for uid, email, name, role, pwd in users:
            existing = await u_repo.get(uid)
            if existing is None:
                await u_repo.create(
                    User(
                        id=uid,
                        tenant_id="t_demo",
                        email=email,
                        display_name=name,
                        role=role,
                        hashed_password=PasswordHasher.hash(pwd),
                    )
                )

        hosts = [
            ("h_alice", "Alice 主播", "douyin_1001"),
            ("h_bob", "Bob 主播", "kuaishou_2002"),
            ("h_cathy", "Cathy 主播", None),
        ]
        host_ids = []
        for hid, name, ext in hosts:
            if await h_repo.get(hid) is None:
                await h_repo.create(
                    Host(
                        id=hid,
                        tenant_id="t_demo",
                        display_name=name,
                        external_id=ext,
                        consent_signed_at=datetime.now(UTC) - timedelta(days=7),
                        face_enrolled_at=datetime.now(UTC) - timedelta(days=7),
                        voice_enrolled_at=datetime.now(UTC) - timedelta(days=7),
                    )
                )
            host_ids.append(hid)

        streams = [
            ("str_demo_douyin", "douyin", "rtmp://push.douyin.com/live/demoAlice", "h_alice"),
            ("str_demo_ks", "kuaishou", "rtmp://push.kuaishou.com/live/demoBob", "h_bob"),
            ("str_demo_custom", "custom", "rtmp://push.example.com/live/demoCathy", "h_cathy"),
        ]
        for sid, plat, url, hid in streams:
            if await str_repo.get(sid) is None:
                await str_repo.create(
                    Stream(
                        id=sid,
                        tenant_id="t_demo",
                        host_id=hid,
                        platform=plat,
                        rtmp_url=url,
                        status=StreamStatus.ACTIVE,
                        last_state="ON_DUTY",
                        last_fusion_score=0.82,
                        last_heartbeat_at=datetime.now(UTC),
                    )
                )

        now = datetime.now(UTC)
        demo_events = [
            EventRecord(
                id=f"evt_{uuid4().hex[:20]}",
                tenant_id="t_demo",
                stream_id="str_demo_douyin",
                host_id="h_alice",
                event_type="lvg.host.online.v1",
                from_state="IDLE",
                to_state="ON_DUTY",
                fusion_score=0.82,
                severity=Severity.INFO,
                signal_breakdown={"face": 0.95, "person": 0.9, "reid": 0.85},
                weights_used={"face": 0.30, "person": 0.20, "reid": 0.20},
                duration_offline_s=0.0,
                created_at=now - timedelta(hours=3),
            ),
            EventRecord(
                id=f"evt_{uuid4().hex[:20]}",
                tenant_id="t_demo",
                stream_id="str_demo_ks",
                host_id="h_bob",
                event_type="lvg.alert.host_offline.v1",
                from_state="BRIEF_AWAY",
                to_state="LONG_AWAY",
                fusion_score=0.21,
                severity=Severity.P1,
                duration_offline_s=65.0,
                created_at=now - timedelta(minutes=45),
            ),
            EventRecord(
                id=f"evt_{uuid4().hex[:20]}",
                tenant_id="t_demo",
                stream_id="str_demo_custom",
                host_id="h_cathy",
                event_type="lvg.cheat.deepfake_avatar.v1",
                from_state="ANY",
                to_state="CHEAT_FLAGGED",
                fusion_score=0.87,
                severity=Severity.P0,
                extras={"pattern": "DEEPFAKE_AVATAR", "deepfake_score": 0.87},
                created_at=now - timedelta(minutes=10),
            ),
        ]
        for e in demo_events:
            await ev_repo.add(e)

        await al_repo.add(
            Alert(
                id=f"alt_{uuid4().hex[:20]}",
                tenant_id="t_demo",
                stream_id="str_demo_ks",
                host_id="h_bob",
                severity=Severity.P1,
                state=AlertState.OPEN,
                event_ids=[demo_events[1].id],
                title="主播离岗 ≥ 60s · str_demo_ks",
                summary="状态: BRIEF_AWAY → LONG_AWAY ｜ 融合得分: 0.210 ｜ 累计离开: 65.0s",
                first_seen_at=now - timedelta(minutes=45),
            )
        )

        await s.commit()
        print("[seed] DemoShop 旗舰店 + 3 主播 + 3 直播 + 3 事件 + 1 告警 已写入")


if __name__ == "__main__":
    asyncio.run(seed())
