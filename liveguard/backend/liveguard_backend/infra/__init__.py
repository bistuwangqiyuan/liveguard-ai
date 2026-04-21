"""基础设施适配器：Kafka / Redis / Metrics / Tracing。"""
from .bus import EventBus, InMemoryEventBus, KafkaEventBus
from .cache import CacheClient, InMemoryCache, RedisCache
from .metrics import (
    ALERTS_TOTAL,
    API_LATENCY,
    EVENTS_TOTAL,
    INGEST_TOTAL,
    metrics_response,
)

__all__ = [
    "ALERTS_TOTAL",
    "API_LATENCY",
    "CacheClient",
    "EVENTS_TOTAL",
    "EventBus",
    "INGEST_TOTAL",
    "InMemoryCache",
    "InMemoryEventBus",
    "KafkaEventBus",
    "RedisCache",
    "metrics_response",
]
