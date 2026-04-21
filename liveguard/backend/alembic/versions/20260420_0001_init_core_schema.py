"""init core schema

Revision ID: 0001_init
Revises: 
Create Date: 2026-04-20 00:00:00.000000

完整初始 DDL — 对应 ``Design §7 Data Model``。

SQLite 兼容；生产 Postgres 会在部署时手工补：
* ``CREATE EXTENSION pgvector``（主播人脸/声纹 embedding）
* Row-Level Security policies（租户隔离）
* pg_partman 按月分区 ``events`` 表
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False, server_default="starter"),
        sa.Column("region", sa.String(32), server_default="cn-east-1"),
        sa.Column("privacy_mode", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("dpa_signed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("display_name", sa.String(128), server_default=""),
        sa.Column("role", sa.String(32), server_default="viewer"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("mfa_enrolled", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_tenant_email", "users", ["tenant_id", "email"], unique=True)

    op.create_table(
        "hosts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("external_id", sa.String(128)),
        sa.Column("face_vector_version", sa.String(64), server_default=""),
        sa.Column("voice_vector_version", sa.String(64), server_default=""),
        sa.Column("consent_signed_at", sa.DateTime(timezone=True)),
        sa.Column("face_enrolled_at", sa.DateTime(timezone=True)),
        sa.Column("voice_enrolled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hosts_tenant", "hosts", ["tenant_id"])

    op.create_table(
        "streams",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("host_id", sa.String(36), sa.ForeignKey("hosts.id")),
        sa.Column("platform", sa.String(32), server_default="custom"),
        sa.Column("rtmp_url", sa.Text),
        sa.Column("status", sa.String(16), server_default="inactive"),
        sa.Column("schedule_cron", sa.String(64)),
        sa.Column("last_state", sa.String(32), server_default="IDLE"),
        sa.Column("last_fusion_score", sa.Float, server_default="0.0"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_streams_tenant", "streams", ["tenant_id"])
    op.create_index("ix_streams_host", "streams", ["host_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("stream_id", sa.String(36), nullable=False),
        sa.Column("host_id", sa.String(36)),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("from_state", sa.String(32)),
        sa.Column("to_state", sa.String(32)),
        sa.Column("fusion_score", sa.Float, server_default="0.0"),
        sa.Column("severity", sa.String(8), server_default="INFO"),
        sa.Column("signal_breakdown", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("weights_used", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("duration_offline_s", sa.Float, server_default="0.0"),
        sa.Column("extras", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_events_stream_time", "events", ["stream_id", "created_at"])
    op.create_index("ix_events_tenant_time", "events", ["tenant_id", "created_at"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("stream_id", sa.String(36), nullable=False),
        sa.Column("host_id", sa.String(36)),
        sa.Column("severity", sa.String(8), server_default="INFO"),
        sa.Column("state", sa.String(16), server_default="open"),
        sa.Column("event_ids", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text, server_default=""),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ack_by", sa.String(36)),
        sa.Column("ack_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("evidence_uri", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_tenant_state", "alerts", ["tenant_id", "state"])
    op.create_index("ix_alerts_stream", "alerts", ["stream_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("label", sa.String(128), server_default=""),
        sa.Column("scopes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "usage_counters",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("bucket_hour", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stream_minutes", sa.Float, server_default="0.0"),
        sa.Column("events_count", sa.Integer, server_default="0"),
        sa.Column("alerts_count", sa.Integer, server_default="0"),
        sa.Column("notifications_count", sa.Integer, server_default="0"),
    )
    op.create_index(
        "ix_usage_tenant_bucket",
        "usage_counters",
        ["tenant_id", "bucket_hour"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_usage_tenant_bucket", table_name="usage_counters")
    op.drop_table("usage_counters")
    op.drop_table("api_keys")
    op.drop_index("ix_alerts_stream", table_name="alerts")
    op.drop_index("ix_alerts_tenant_state", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_events_tenant_time", table_name="events")
    op.drop_index("ix_events_stream_time", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_streams_host", table_name="streams")
    op.drop_index("ix_streams_tenant", table_name="streams")
    op.drop_table("streams")
    op.drop_index("ix_hosts_tenant", table_name="hosts")
    op.drop_table("hosts")
    op.drop_index("ix_users_tenant_email", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")
