"""RBAC — 角色 × 资源矩阵。"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable

from fastapi import HTTPException, status

from ..domain.enums import Role
from .auth import AuthContext

# Role 层级：OWNER > ADMIN > OPERATOR > VIEWER > API
_ROLE_ORDER = {
    Role.OWNER: 40,
    Role.ADMIN: 30,
    Role.OPERATOR: 20,
    Role.VIEWER: 10,
    Role.API: 10,
}


def _rank(r: Role) -> int:
    return _ROLE_ORDER.get(r, 0)


def require_role(min_role: Role, *, any_of: Iterable[Role] = ()) -> Callable[..., Any]:
    """FastAPI 依赖：要求至少 ``min_role`` 级别，或 ``any_of`` 命中。"""

    def dep(auth: AuthContext) -> AuthContext:
        if any_of and auth.role in any_of:
            return auth
        if _rank(auth.role) < _rank(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role {auth.role.value} insufficient (need ≥ {min_role.value})",
            )
        return auth

    return dep


def tenant_scoped(auth: AuthContext, tenant_id: str) -> None:
    """强制租户隔离 — 任何跨租户访问直接 403。"""
    if auth.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cross-tenant access denied",
        )
