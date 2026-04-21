"""认证路由：登录、登出、刷新（demo 简化实现）。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...config import get_settings
from ...db.repositories import UserRepo
from ...domain.enums import Role
from ...security.auth import PasswordHasher, create_access_token, decode_token
from ..deps import SessionDep
from ..schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse, summary="user password login")
async def login(req: LoginRequest, session: SessionDep) -> TokenResponse:
    settings = get_settings()
    repo = UserRepo(session)
    user = await repo.get_by_email(req.tenant_id, req.email)
    if user is None or not user.hashed_password or not PasswordHasher.verify(
        req.password, user.hashed_password
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user disabled")
    token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        scopes=("streams:read", "events:read", "alerts:ack"),
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_ttl_s)


@router.post("/refresh", response_model=TokenResponse, summary="refresh token")
async def refresh(authorization: str) -> TokenResponse:
    # Demo 实现：要求 bearer token，重新签发。生产走 refresh_token 专用流程。
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="need bearer token")
    try:
        ctx = decode_token(authorization.split(maxsplit=1)[1])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    new_tok = create_access_token(
        subject=ctx.subject, tenant_id=ctx.tenant_id, role=Role(ctx.role), scopes=ctx.scopes
    )
    return TokenResponse(access_token=new_tok, expires_in=get_settings().jwt_ttl_s)
