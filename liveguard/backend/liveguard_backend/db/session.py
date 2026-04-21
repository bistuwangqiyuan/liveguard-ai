"""
liveguard_backend.db.session
============================

SQLAlchemy 2.0 async engine + session factory.

默认使用 ``sqlite+aiosqlite`` 便于离线 demo；生产使用 ``postgresql+asyncpg://``。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ..config import get_settings


class Base(DeclarativeBase):
    """所有 ORM 模型共同基类。"""
    pass


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as sess:
        try:
            yield sess
        except Exception:
            await sess.rollback()
            raise


async def init_db() -> None:
    """开发环境建表 — 生产走 Alembic。"""
    from . import orm  # noqa: F401 — ensure tables registered

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
