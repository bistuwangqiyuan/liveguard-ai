"""边缘信号摄取路由 + WebSocket 实时推送。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from ...db.repositories import EventRepo, StreamRepo
from ...domain.models import SignalIngest
from ..deps import (
    AlertManagerDep,
    AuthDep,
    IngestServiceDep,
    SessionDep,
)
from ..schemas import IngestAck, SignalIngestRequest

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


@router.post("/signals", response_model=IngestAck, status_code=status.HTTP_202_ACCEPTED)
async def ingest_signal(
    req: SignalIngestRequest,
    session: SessionDep,
    auth: AuthDep,
    svc: IngestServiceDep,
    alerts: AlertManagerDep,
) -> IngestAck:
    signal = SignalIngest(**req.model_dump())
    result = await svc.ingest(signal, tenant_id=auth.tenant_id)

    # 持久化事件
    repo = EventRepo(session)
    stream_repo = StreamRepo(session)
    from ...domain.models import EventRecord

    for ev_dict in result["events_emitted"]:
        await repo.add(EventRecord.model_validate(ev_dict))
        # 用同一个 dict 驱动 AlertManager
        await alerts.on_event(EventRecord.model_validate(ev_dict))

    await stream_repo.update_state(signal.stream_id, result["state"], result["fusion_score"])
    await session.commit()

    # 推给 WebSocket 订阅者
    await _broadcast_hub.publish(signal.stream_id, result)

    return IngestAck(
        stream_id=result["stream_id"],
        state=result["state"],
        fusion_score=result["fusion_score"],
        offline_seconds=result["offline_seconds"],
        state_event=result["state_event"],
        cheat_flags=result["cheat_flags"],
    )


# ---------------------------------------------------------------------------
# WebSocket 订阅 — stream 维度的实时推送
# ---------------------------------------------------------------------------


class _Hub:
    def __init__(self) -> None:
        self._subs: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add(self, stream_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[stream_id].add(ws)

    async def remove(self, stream_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[stream_id].discard(ws)
            if not self._subs[stream_id]:
                self._subs.pop(stream_id, None)

    async def publish(self, stream_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._subs.get(stream_id, ()))
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 — 订阅者可能已断开
                await self.remove(stream_id, ws)


_broadcast_hub = _Hub()


ws_router = APIRouter(tags=["realtime"])


@ws_router.websocket("/ws/v1/streams/{stream_id}")
async def stream_ws(ws: WebSocket, stream_id: str) -> None:
    await ws.accept()
    await _broadcast_hub.add(stream_id, ws)
    try:
        while True:
            # 客户端可发送 ping；这里只做心跳保活
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        await _broadcast_hub.remove(stream_id, ws)
