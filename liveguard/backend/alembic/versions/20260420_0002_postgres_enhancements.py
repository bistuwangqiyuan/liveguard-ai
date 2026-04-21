"""postgres enhancements (pgvector, RLS, partitioning)

Revision ID: 0002_pg_enh
Revises: 0001_init
Create Date: 2026-04-20 00:10:00.000000

仅在 PostgreSQL 上执行 — SQLite / 其他方言下跳过。
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_pg_enh"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    # 1. 启用扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS pgvector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 2. 为 hosts 增加人脸 / 声纹向量列
    op.execute(
        """
        ALTER TABLE hosts
          ADD COLUMN IF NOT EXISTS face_vector vector(128),
          ADD COLUMN IF NOT EXISTS voice_vector vector(192)
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_hosts_face_vector "
        "ON hosts USING ivfflat (face_vector vector_cosine_ops) WITH (lists = 100)"
    )

    # 3. 多租户行级安全 (RLS)
    op.execute("ALTER TABLE streams ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE events  ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE alerts  ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE hosts   ENABLE ROW LEVEL SECURITY")

    for tbl in ("streams", "events", "alerts", "hosts"):
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{tbl}
              ON {tbl}
              USING (tenant_id = current_setting('app.tenant_id', true))
              WITH CHECK (tenant_id = current_setting('app.tenant_id', true))
            """
        )

    # 4. events 表按月分区（仅结构；生产用 pg_partman 自动创建分区）
    op.execute("ALTER TABLE events RENAME TO events_legacy")
    op.execute(
        """
        CREATE TABLE events (
          id text PRIMARY KEY,
          tenant_id text NOT NULL,
          stream_id text NOT NULL,
          host_id text,
          event_type text NOT NULL,
          from_state text,
          to_state text,
          fusion_score double precision DEFAULT 0,
          severity text DEFAULT 'INFO',
          signal_breakdown jsonb NOT NULL DEFAULT '{}'::jsonb,
          weights_used jsonb NOT NULL DEFAULT '{}'::jsonb,
          duration_offline_s double precision DEFAULT 0,
          extras jsonb NOT NULL DEFAULT '{}'::jsonb,
          created_at timestamptz NOT NULL DEFAULT now()
        ) PARTITION BY RANGE (created_at)
        """
    )
    op.execute(
        "CREATE TABLE events_y2026m04 PARTITION OF events "
        "FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')"
    )
    op.execute(
        "CREATE TABLE events_y2026m05 PARTITION OF events "
        "FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')"
    )
    op.execute("INSERT INTO events SELECT * FROM events_legacy")
    op.execute("DROP TABLE events_legacy")
    op.execute("CREATE INDEX ix_events_stream_time ON events (stream_id, created_at DESC)")
    op.execute("CREATE INDEX ix_events_tenant_time ON events (tenant_id, created_at DESC)")


def downgrade() -> None:
    if not _is_postgres():
        return
    for tbl in ("streams", "events", "alerts", "hosts"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{tbl} ON {tbl}")
        op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY")
