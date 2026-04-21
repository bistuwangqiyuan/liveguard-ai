"""仓储层 — 屏蔽 ORM 细节，返回领域模型。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.enums import AlertState
from ..domain.models import Alert, EventRecord, Host, Stream, Tenant, User
from . import orm


class TenantRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def get(self, tenant_id: str) -> Tenant | None:
        row = await self.s.get(orm.TenantORM, tenant_id)
        return Tenant.model_validate(row) if row else None

    async def list(self, limit: int = 50) -> list[Tenant]:
        rows = (await self.s.execute(select(orm.TenantORM).limit(limit))).scalars().all()
        return [Tenant.model_validate(r) for r in rows]

    async def create(self, t: Tenant) -> Tenant:
        row = orm.TenantORM(**t.model_dump())
        self.s.add(row)
        await self.s.flush()
        return Tenant.model_validate(row)


class UserRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def get_by_email(self, tenant_id: str, email: str) -> User | None:
        stmt = select(orm.UserORM).where(
            orm.UserORM.tenant_id == tenant_id,
            orm.UserORM.email == email,
        )
        row = (await self.s.execute(stmt)).scalar_one_or_none()
        return User.model_validate(row) if row else None

    async def get(self, user_id: str) -> User | None:
        row = await self.s.get(orm.UserORM, user_id)
        return User.model_validate(row) if row else None

    async def create(self, u: User) -> User:
        row = orm.UserORM(**u.model_dump())
        self.s.add(row)
        await self.s.flush()
        return User.model_validate(row)


class HostRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def get(self, host_id: str) -> Host | None:
        row = await self.s.get(orm.HostORM, host_id)
        return Host.model_validate(row) if row else None

    async def list(self, tenant_id: str, limit: int = 100) -> list[Host]:
        stmt = select(orm.HostORM).where(orm.HostORM.tenant_id == tenant_id).limit(limit)
        rows = (await self.s.execute(stmt)).scalars().all()
        return [Host.model_validate(r) for r in rows]

    async def create(self, h: Host) -> Host:
        row = orm.HostORM(**h.model_dump())
        self.s.add(row)
        await self.s.flush()
        return Host.model_validate(row)


class StreamRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def get(self, stream_id: str) -> Stream | None:
        row = await self.s.get(orm.StreamORM, stream_id)
        return Stream.model_validate(row) if row else None

    async def list(self, tenant_id: str, limit: int = 100) -> list[Stream]:
        stmt = (
            select(orm.StreamORM)
            .where(orm.StreamORM.tenant_id == tenant_id)
            .order_by(desc(orm.StreamORM.created_at))
            .limit(limit)
        )
        rows = (await self.s.execute(stmt)).scalars().all()
        return [Stream.model_validate(r) for r in rows]

    async def create(self, stream: Stream) -> Stream:
        row = orm.StreamORM(**stream.model_dump())
        self.s.add(row)
        await self.s.flush()
        return Stream.model_validate(row)

    async def update_state(self, stream_id: str, state: str, score: float) -> None:
        row = await self.s.get(orm.StreamORM, stream_id)
        if row is None:
            return
        row.last_state = state
        row.last_fusion_score = score
        row.last_heartbeat_at = datetime.now(UTC)


class EventRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def add(self, e: EventRecord) -> None:
        self.s.add(orm.EventORM(**e.model_dump()))

    async def add_many(self, events: Sequence[EventRecord]) -> None:
        self.s.add_all(orm.EventORM(**e.model_dump()) for e in events)

    async def list(self, tenant_id: str, stream_id: str | None, limit: int = 100) -> list[EventRecord]:
        stmt = select(orm.EventORM).where(orm.EventORM.tenant_id == tenant_id)
        if stream_id:
            stmt = stmt.where(orm.EventORM.stream_id == stream_id)
        stmt = stmt.order_by(desc(orm.EventORM.created_at)).limit(limit)
        rows = (await self.s.execute(stmt)).scalars().all()
        return [EventRecord.model_validate(r) for r in rows]


class AlertRepo:
    def __init__(self, sess: AsyncSession) -> None:
        self.s = sess

    async def add(self, a: Alert) -> Alert:
        row = orm.AlertORM(**a.model_dump())
        self.s.add(row)
        await self.s.flush()
        return Alert.model_validate(row)

    async def list_open(self, tenant_id: str, limit: int = 100) -> list[Alert]:
        stmt = (
            select(orm.AlertORM)
            .where(
                orm.AlertORM.tenant_id == tenant_id,
                orm.AlertORM.state == AlertState.OPEN.value,
            )
            .order_by(desc(orm.AlertORM.first_seen_at))
            .limit(limit)
        )
        rows = (await self.s.execute(stmt)).scalars().all()
        return [Alert.model_validate(r) for r in rows]

    async def ack(self, alert_id: str, user_id: str) -> Alert | None:
        row = await self.s.get(orm.AlertORM, alert_id)
        if row is None:
            return None
        row.state = AlertState.ACKED.value
        row.ack_by = user_id
        row.ack_at = datetime.now(UTC)
        return Alert.model_validate(row)

    async def resolve(self, alert_id: str) -> Alert | None:
        row = await self.s.get(orm.AlertORM, alert_id)
        if row is None:
            return None
        row.state = AlertState.RESOLVED.value
        row.resolved_at = datetime.now(UTC)
        return Alert.model_validate(row)
