"""Redis 缓存 + 内存 fallback。"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

try:
    from redis.asyncio import Redis  # type: ignore
    _HAS_REDIS = True
except ImportError:  # pragma: no cover
    _HAS_REDIS = False


class CacheClient(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...
    @abstractmethod
    async def set(self, key: str, value: str, ttl_s: int | None = None) -> None: ...
    @abstractmethod
    async def delete(self, key: str) -> None: ...
    @abstractmethod
    async def incr(self, key: str, by: int = 1) -> int: ...
    @abstractmethod
    async def close(self) -> None: ...


class InMemoryCache(CacheClient):
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> str | None:
        async with self._lock:
            v = self._store.get(key)
            if v is None:
                return None
            val, exp = v
            if exp is not None and time.time() > exp:
                self._store.pop(key, None)
                return None
            return val

    async def set(self, key: str, value: str, ttl_s: int | None = None) -> None:
        exp = (time.time() + ttl_s) if ttl_s else None
        async with self._lock:
            self._store[key] = (value, exp)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def incr(self, key: str, by: int = 1) -> int:
        async with self._lock:
            cur = self._store.get(key)
            n = int(cur[0]) if cur else 0
            n += by
            self._store[key] = (str(n), cur[1] if cur else None)
            return n

    async def close(self) -> None:
        return None


class RedisCache(CacheClient):
    def __init__(self, url: str) -> None:
        if not _HAS_REDIS:
            raise RuntimeError("redis not installed; install liveguard-backend[dev] extras")
        self._client: Redis = Redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_s: int | None = None) -> None:
        if ttl_s:
            await self._client.set(key, value, ex=ttl_s)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def incr(self, key: str, by: int = 1) -> int:
        return int(await self._client.incrby(key, by))

    async def close(self) -> None:
        await self._client.close()
