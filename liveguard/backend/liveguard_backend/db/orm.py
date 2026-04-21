"""
liveguard_backend.db.orm
========================

ORM 表定义（SQLAlchemy 2.0 typed）。

注意：SQLite 兼容性 — 用 JSON 取代 JSONB、用 String(36) 存 UUID。生产 Postgres
通过 Alembic 迁移脚本可切换到 UUID/JSONB/pgvector。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


def _now() -> Any:
    return func.now()


class TenantORM(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    plan: Mapped[str] = mapped_column(String(32), default="starter", nullable=False)
    region: Mapped[str] = mapped_column(String(32), default="cn-east-1")
    privacy_mode: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dpa_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now(), onupdate=_now())


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_tenant_email", "tenant_id", "email", unique=True),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(128), default="")
    role: Mapped[str] = mapped_column(String(32), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enrolled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())


class HostORM(Base):
    __tablename__ = "hosts"
    __table_args__ = (
        Index("ix_hosts_tenant", "tenant_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    face_vector_version: Mapped[str] = mapped_column(String(64), default="")
    voice_vector_version: Mapped[str] = mapped_column(String(64), default="")
    consent_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    face_enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    voice_enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())


class StreamORM(Base):
    __tablename__ = "streams"
    __table_args__ = (
        Index("ix_streams_tenant", "tenant_id"),
        Index("ix_streams_host", "host_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    host_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("hosts.id"))
    platform: Mapped[str] = mapped_column(String(32), default="custom")
    rtmp_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="inactive")
    schedule_cron: Mapped[str | None] = mapped_column(String(64))
    last_state: Mapped[str] = mapped_column(String(32), default="IDLE")
    last_fusion_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())


class EventORM(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_stream_time", "stream_id", "created_at"),
        Index("ix_events_tenant_time", "tenant_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    stream_id: Mapped[str] = mapped_column(String(36), nullable=False)
    host_id: Mapped[str | None] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_state: Mapped[str] = mapped_column(String(32))
    to_state: Mapped[str] = mapped_column(String(32))
    fusion_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(8), default="INFO")
    signal_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    weights_used: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    duration_offline_s: Mapped[float] = mapped_column(Float, default=0.0)
    extras: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())


class AlertORM(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_tenant_state", "tenant_id", "state"),
        Index("ix_alerts_stream", "stream_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    stream_id: Mapped[str] = mapped_column(String(36), nullable=False)
    host_id: Mapped[str | None] = mapped_column(String(36))
    severity: Mapped[str] = mapped_column(String(8), default="INFO")
    state: Mapped[str] = mapped_column(String(16), default="open")
    event_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    ack_by: Mapped[str | None] = mapped_column(String(36))
    ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_uri: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())


class ApiKeyORM(Base):
    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"))
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), default="")
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=_now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsageCounterORM(Base):
    """按小时桶的计量表 — 便于对账与出具发票。"""
    __tablename__ = "usage_counters"
    __table_args__ = (
        Index("ix_usage_tenant_bucket", "tenant_id", "bucket_hour", unique=True),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    bucket_hour: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stream_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    events_count: Mapped[int] = mapped_column(default=0)
    alerts_count: Mapped[int] = mapped_column(default=0)
    notifications_count: Mapped[int] = mapped_column(default=0)
