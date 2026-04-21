"""上行信号到 backend — 批处理 + 重试。"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx
import structlog
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class UploaderConfig:
    base_url: str
    token: str
    path: str = "/v1/ingest/signals"
    timeout_s: float = 6.0
    max_inflight: int = 32
    max_retries: int = 3


class SignalUploader:
    def __init__(self, cfg: UploaderConfig, *, client: httpx.AsyncClient | None = None) -> None:
        self._cfg = cfg
        self._client = client or httpx.AsyncClient(timeout=cfg.timeout_s)
        self._sem = asyncio.Semaphore(cfg.max_inflight)

    async def upload(self, payload: dict) -> dict:
        async with self._sem:
            return await self._upload_one(payload)

    async def _upload_one(self, payload: dict) -> dict:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._cfg.max_retries + 1),
            wait=wait_exponential(multiplier=0.25, max=4.0),
            retry=retry_if_exception_type((httpx.HTTPError, RuntimeError)),
            reraise=True,
        ):
            with attempt:
                t0 = time.perf_counter()
                r = await self._client.post(
                    f"{self._cfg.base_url.rstrip('/')}{self._cfg.path}",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._cfg.token}"},
                )
                if r.status_code >= 500:
                    raise RuntimeError(f"server {r.status_code}")
                if r.status_code >= 400:
                    log.warning("uploader.client_error", status=r.status_code, body=r.text[:200])
                    return {"ok": False, "status": r.status_code}
                elapsed = (time.perf_counter() - t0) * 1000.0
                data = r.json()
                log.info("uploader.ok", latency_ms=f"{elapsed:.1f}",
                         state=data.get("state"), score=data.get("fusion_score"))
                return {"ok": True, "latency_ms": elapsed, **data}
        return {"ok": False}

    async def aclose(self) -> None:
        await self._client.aclose()
