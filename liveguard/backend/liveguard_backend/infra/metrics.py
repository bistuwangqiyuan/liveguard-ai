"""Prometheus metrics — ``Design §12 Observability``。"""

from __future__ import annotations

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

INGEST_TOTAL = Counter(
    "lvg_ingest_signals_total",
    "Signal frames ingested",
    labelnames=("tenant", "status"),
)

EVENTS_TOTAL = Counter(
    "lvg_events_total",
    "State-transition events emitted",
    labelnames=("tenant", "severity"),
)

ALERTS_TOTAL = Counter(
    "lvg_alerts_total",
    "Alerts created",
    labelnames=("tenant", "severity", "state"),
)

API_LATENCY = Histogram(
    "lvg_api_latency_seconds",
    "API handler latency",
    labelnames=("route", "method", "status"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

ACTIVE_STREAMS = Gauge(
    "lvg_active_streams",
    "Active streams currently in ON_DUTY / BRIEF_AWAY",
    labelnames=("tenant",),
)

ALGO_LATENCY = Histogram(
    "lvg_algo_latency_ms",
    "Algorithm pipeline frame latency (ms)",
    labelnames=("model",),
    buckets=(2, 5, 10, 20, 50, 100, 200, 500, 1000),
)


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
