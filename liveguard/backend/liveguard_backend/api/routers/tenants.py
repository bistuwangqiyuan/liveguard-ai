"""租户管理。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ...db.repositories import TenantRepo, UserRepo
from ...domain.enums import Role
from ...domain.models import Tenant, User
from ...security.auth import PasswordHasher
from ..deps import AuthDep, SessionDep
from ..schemas import TenantCreateRequest, TenantRead, UserCreateRequest, UserRead

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantRead])
async def list_tenants(session: SessionDep, auth: AuthDep) -> list[TenantRead]:
    if auth.role != Role.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner only")
    tenants = await TenantRepo(session).list()
    return [TenantRead.model_validate(t.model_dump()) for t in tenants]


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(req: TenantCreateRequest, session: SessionDep, auth: AuthDep) -> TenantRead:
    if auth.role != Role.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner only")
    created = await TenantRepo(session).create(Tenant(**req.model_dump()))
    await session.commit()
    return TenantRead.model_validate(created.model_dump())


@router.post(
    "/{tenant_id}/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="add user to tenant",
)
async def add_user(
    tenant_id: str, req: UserCreateRequest, session: SessionDep, auth: AuthDep
) -> UserRead:
    if auth.role not in (Role.OWNER, Role.ADMIN) or (auth.role == Role.ADMIN and auth.tenant_id != tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient role")
    from uuid import uuid4

    user = User(
        id=f"usr_{uuid4().hex[:24]}",
        tenant_id=tenant_id,
        email=req.email,
        hashed_password=PasswordHasher.hash(req.password),
        display_name=req.display_name,
        role=req.role,
    )
    created = await UserRepo(session).create(user)
    await session.commit()
    return UserRead.model_validate(created.model_dump())
