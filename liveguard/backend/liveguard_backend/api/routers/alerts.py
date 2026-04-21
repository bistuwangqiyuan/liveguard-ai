"""告警路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...db.repositories import AlertRepo
from ..deps import AuthDep, SessionDep
from ..schemas import AlertAckRequest, AlertRead

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
async def list_open_alerts(session: SessionDep, auth: AuthDep) -> list[AlertRead]:
    alerts = await AlertRepo(session).list_open(auth.tenant_id)
    return [AlertRead.model_validate(a.model_dump()) for a in alerts]


@router.post("/{alert_id}/ack", response_model=AlertRead)
async def ack_alert(alert_id: str, _req: AlertAckRequest, session: SessionDep, auth: AuthDep) -> AlertRead:
    alert = await AlertRepo(session).ack(alert_id, auth.subject)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    if alert.tenant_id != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cross-tenant denied")
    await session.commit()
    return AlertRead.model_validate(alert.model_dump())


@router.post("/{alert_id}/resolve", response_model=AlertRead)
async def resolve_alert(alert_id: str, session: SessionDep, auth: AuthDep) -> AlertRead:
    alert = await AlertRepo(session).resolve(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert not found")
    if alert.tenant_id != auth.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cross-tenant denied")
    await session.commit()
    return AlertRead.model_validate(alert.model_dump())
