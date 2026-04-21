"""
liveguard_backend.infra.bus
===========================

事件总线抽象 — 对应 ``Design §4.2 Kafka Topology``。

* :class:`KafkaEventBus`：生产使用 aiokafka。
* :class:`InMemoryEventBus`：单元测试与本地 demo 使用，语义上与 Kafka 等价但
  只在进程内传递。
"""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Awaitable, Callable

import orjson

try:
    from aiokafka import AIOKafkaProducer  # type: ignore
    _HAS_KAFKA = True
except ImportError:  # pragma: no cover
    _HAS_KAFKA = False


class EventBus(ABC):
    @abstractmethod
    async def start(self) -> None: ...
    @abstractmethod
    async def stop(self) -> None: ...
    @abstractmethod
    async def publish(self, topic: str, payload: dict[str, Any], *, key: str | None = None) -> None: ...
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None: ...


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = defaultdict(list)
        self._published: list[tuple[str, dict[str, Any]]] = []
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def publish(self, topic: str, payload: dict[str, Any], *, key: str | None = None) -> None:
        async with self._lock:
            self._published.append((topic, payload))
        for h in list(self._handlers.get(topic, ())):
            await h(payload)

    async def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._handlers[topic].append(handler)

    @property
    def published(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self._published)


class KafkaEventBus(EventBus):
    def __init__(self, bootstrap_servers: str, client_id: str = "liveguard-backend") -> None:
        if not _HAS_KAFKA:
            raise RuntimeError("aiokafka not installed; install liveguard-backend[dev] or aiokafka.")
        self._bootstrap = bootstrap_servers
        self._client_id = client_id
        self._producer: AIOKafkaProducer | None = None
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = defaultdict(list)

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap,
            client_id=self._client_id,
            acks="all",
            enable_idempotence=True,
            compression_type="lz4",
            value_serializer=lambda v: orjson.dumps(v),
            key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def publish(self, topic: str, payload: dict[str, Any], *, key: str | None = None) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventBus not started")
        await self._producer.send_and_wait(topic, payload, key=key)

    async def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        # 生产中用独立的 consumer worker；这里保留 API 对齐。
        self._handlers[topic].append(handler)


def format_cloudevent(
    *, event_id: str, type_: str, source: str, subject: str, data: dict[str, Any]
) -> dict[str, Any]:
    """CloudEvents 1.0 兼容 envelope（Kafka 消息体）。"""
    import datetime as _dt
    return {
        "specversion": "1.0",
        "id": event_id,
        "type": type_,
        "source": source,
        "subject": subject,
        "time": _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds"),
        "datacontenttype": "application/json",
        "data": data,
    }
