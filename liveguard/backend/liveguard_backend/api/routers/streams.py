"""直播流与事件路由。"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from ...db.repositories import EventRepo, StreamRepo
from ...domain.models import Stream
from ..deps import AuthDep, SessionDep
from ..schemas import EventRead, StreamCreateRequest, StreamRead

router = APIRouter(prefix="/v1/streams", tags=["streams"])


@router.get("", response_model=list[StreamRead])
async def list_streams(session: SessionDep, auth: AuthDep, limit: int = Query(100, ge=1, le=500)) -> list[StreamRead]:
    streams = await StreamRepo(session).list(auth.tenant_id, limit=limit)
    return [StreamRead.model_validate(s.model_dump()) for s in streams]


@router.post("", response_model=StreamRead, status_code=status.HTTP_201_CREATED)
async def create_stream(req: StreamCreateRequest, session: SessionDep, auth: AuthDep) -> StreamRead:
    stream = Stream(
        id=f"str_{uuid4().hex[:24]}",
        tenant_id=auth.tenant_id,
        platform=req.platform,
        rtmp_url=req.rtmp_url,
        host_id=req.host_id,
        schedule_cron=req.schedule_cron,
    )
    created = await StreamRepo(session).create(stream)
    await session.commit()
    return StreamRead.model_validate(created.model_dump())


@router.get("/{stream_id}", response_model=StreamRead)
async def get_stream(stream_id: str, session: SessionDep, auth: AuthDep) -> StreamRead:
    stream = await StreamRepo(session).get(stream_id)
    if stream is None or stream.tenant_id != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stream not found")
    return StreamRead.model_validate(stream.model_dump())


@router.get("/{stream_id}/events", response_model=list[EventRead])
async def list_events(
    stream_id: str, session: SessionDep, auth: AuthDep, limit: int = Query(100, ge=1, le=1000)
) -> list[EventRead]:
    events = await EventRepo(session).list(auth.tenant_id, stream_id=stream_id, limit=limit)
    return [EventRead.model_validate(e.model_dump()) for e in events]
