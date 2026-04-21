-- 守播 LiveGuard · 初始化 Postgres 扩展
-- Timescale 基础镜像已带 timescaledb；我们额外启用 pgvector / pg_trgm / uuid-ossp

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- pgvector 可能需要先确保镜像支持；失败则忽略（Alembic 会再尝试）
DO $$ BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'vector extension not available, skip';
END $$;
