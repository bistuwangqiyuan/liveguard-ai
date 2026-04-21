"""Notify HTTP API — 供 backend 同步调用；Kafka consumer 另起协程。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import __version__
from .channels import NotificationJob
from .config import get_settings
from .dispatcher import Dispatcher


class NotifyRequest(BaseModel):
    alert_id: str
    tenant_id: str
    severity: str
    channel: str
    title: str
    summary: str
    stream_id: str
    host_id: str | None = None
    targets: list[str] = Field(default_factory=list)
    retry_policy: dict[str, int] = Field(default_factory=dict)
    extras: dict = Field(default_factory=dict)


class NotifyResponse(BaseModel):
    ok: bool
    channel: str
    latency_ms: float
    attempts: int
    message_id: str | None = None
    error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    dispatcher = Dispatcher()
    app.state.dispatcher = dispatcher
    try:
        yield
    finally:
        await dispatcher.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="LiveGuard Notify", version=__version__, lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok", "service": "liveguard-notify", "version": __version__,
                "timestamp": datetime.now(UTC).isoformat()}

    @app.get("/metrics")
    async def metrics() -> dict:
        return app.state.dispatcher.snapshot()

    @app.post("/v1/send", response_model=NotifyResponse)
    async def send(req: NotifyRequest) -> NotifyResponse:
        job = NotificationJob(
            alert_id=req.alert_id,
            tenant_id=req.tenant_id,
            severity=req.severity,
            channel=req.channel,
            title=req.title,
            summary=req.summary,
            stream_id=req.stream_id,
            host_id=req.host_id,
            targets=list(req.targets),
            retry_policy=dict(req.retry_policy),
            extras=dict(req.extras),
        )
        res = await app.state.dispatcher.dispatch(job)
        return NotifyResponse(
            ok=res.ok, channel=res.channel, latency_ms=res.latency_ms,
            attempts=res.attempts, message_id=res.message_id, error=res.error,
        )

    return app


app = create_app()


def run() -> None:
    s = get_settings()
    uvicorn.run("liveguard_notify.main:app", host=s.http_host, port=s.http_port, log_level=s.log_level.lower())


if __name__ == "__main__":
    run()
