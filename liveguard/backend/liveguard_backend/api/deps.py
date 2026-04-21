"""FastAPI 依赖注入 — Auth / Session / Services。"""

from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..domain.enums import Role
from ..infra.bus import EventBus, InMemoryEventBus
from ..security.auth import AuthContext, decode_token
from ..services import AlertManager, IngestService, StreamFSMStore


async def session_dep() -> AsyncIterator[AsyncSession]:
    async for s in get_session():
        yield s


SessionDep = Annotated[AsyncSession, Depends(session_dep)]


async def current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        return decode_token(authorization.split(maxsplit=1)[1])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


AuthDep = Annotated[AuthContext, Depends(current_user)]


def require_role_dep(min_role: Role):
    async def _dep(auth: AuthDep) -> AuthContext:
        ranks = {Role.OWNER: 40, Role.ADMIN: 30, Role.OPERATOR: 20, Role.VIEWER: 10, Role.API: 10}
        if ranks[auth.role] < ranks[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role {auth.role.value} insufficient (need ≥ {min_role.value})",
            )
        return auth
    return _dep


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus  # type: ignore[no-any-return]


def get_fsm_store(request: Request) -> StreamFSMStore:
    return request.app.state.fsm_store  # type: ignore[no-any-return]


def get_ingest_service(request: Request) -> IngestService:
    return request.app.state.ingest_service  # type: ignore[no-any-return]


def get_alert_manager(request: Request) -> AlertManager:
    return request.app.state.alert_manager  # type: ignore[no-any-return]


EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
FSMStoreDep = Annotated[StreamFSMStore, Depends(get_fsm_store)]
IngestServiceDep = Annotated[IngestService, Depends(get_ingest_service)]
AlertManagerDep = Annotated[AlertManager, Depends(get_alert_manager)]
