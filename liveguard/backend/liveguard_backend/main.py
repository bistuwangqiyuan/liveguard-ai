"""
liveguard_backend.main
======================

FastAPI 应用入口 — ``Design §4 API Gateway``。
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .api.routers import alerts as alerts_router
from .api.routers import auth as auth_router
from .api.routers import health as health_router
from .api.routers import ingest as ingest_router
from .api.routers import streams as streams_router
from .api.routers import tenants as tenants_router
from .config import get_settings
from .db import init_db
from .infra.bus import InMemoryEventBus
from .infra.metrics import API_LATENCY
from .logging_setup import configure_logging, get_logger
from .services import AlertManager, IngestService, NotificationDispatcher, StreamFSMStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging()
    log = get_logger(__name__)

    await init_db()

    bus = InMemoryEventBus()
    await bus.start()
    fsm_store = StreamFSMStore()
    ingest = IngestService(fsm_store, bus)
    dispatcher = NotificationDispatcher(bus)
    alert_mgr = AlertManager(bus, publisher=dispatcher.dispatch)

    app.state.event_bus = bus
    app.state.fsm_store = fsm_store
    app.state.ingest_service = ingest
    app.state.alert_manager = alert_mgr
    app.state.notification_dispatcher = dispatcher

    log.info("liveguard.backend.started", version=__version__, env=settings.env)
    try:
        yield
    finally:
        await bus.stop()
        log.info("liveguard.backend.stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LiveGuard AI · Backend API",
        version=__version__,
        description="守播 LiveGuard AI · 云端 API (OpenAPI 3.1)",
        openapi_url="/v1/openapi.json",
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            API_LATENCY.labels(route=request.url.path, method=request.method, status="500").observe(
                time.perf_counter() - t0
            )
            raise
        elapsed = time.perf_counter() - t0
        API_LATENCY.labels(
            route=request.scope.get("route").path if request.scope.get("route") else request.url.path,
            method=request.method,
            status=str(response.status_code),
        ).observe(elapsed)
        response.headers["X-Response-Time-ms"] = f"{elapsed * 1000:.2f}"
        return response

    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(tenants_router.router)
    app.include_router(streams_router.router)
    app.include_router(alerts_router.router)
    app.include_router(ingest_router.router)
    app.include_router(ingest_router.ws_router)

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "liveguard_backend.main:app",
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower(),
        reload=settings.env == "dev",
    )


if __name__ == "__main__":
    run()
