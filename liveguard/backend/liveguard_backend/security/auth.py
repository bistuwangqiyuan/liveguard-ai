"""
liveguard_backend.security.auth
===============================

认证原语：
* JWT 签发/校验（HS256；生产切换到 RS256 或外接 OIDC Provider）。
* 密码哈希：Argon2id（memory=64MB, time=2, parallelism=2）。
* API Key 哈希：SHA-256（API Key 本身是 32 字节随机，比较 hash 而非明文）。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from ..config import get_settings
from ..domain.enums import Role

_PWD_CTX = CryptContext(schemes=["argon2"], deprecated="auto")


@dataclass(frozen=True, slots=True)
class AuthContext:
    """请求维度的身份信息，注入到 FastAPI 依赖。"""

    subject: str  # user_id or api_key_id
    tenant_id: str
    role: Role
    scopes: tuple[str, ...] = ()
    kind: str = "user"  # "user" | "api_key" | "service"

    def has_scope(self, scope: str) -> bool:
        return "*" in self.scopes or scope in self.scopes


class PasswordHasher:
    @staticmethod
    def hash(password: str) -> str:
        if not password or len(password) < 10:
            raise ValueError("password must be ≥ 10 chars")
        return _PWD_CTX.hash(password)

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        try:
            return _PWD_CTX.verify(password, hashed)
        except Exception:
            return False


class ApiKeyHasher:
    PREFIX = "lvg_"

    @classmethod
    def generate(cls) -> tuple[str, str]:
        """返回 (raw_key, hashed)。raw_key 仅返回一次给用户。"""
        raw = cls.PREFIX + secrets.token_urlsafe(32)
        return raw, cls.hash(raw)

    @staticmethod
    def hash(raw: str) -> str:
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def constant_time_match(cls, raw: str, stored_hash: str) -> bool:
        return hmac.compare_digest(cls.hash(raw), stored_hash)


def create_access_token(
    subject: str,
    tenant_id: str,
    role: Role,
    scopes: tuple[str, ...] = (),
    ttl_s: int | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "tid": tenant_id,
        "role": role.value,
        "scope": " ".join(scopes),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_s or settings.jwt_ttl_s)).timestamp()),
        "iss": "liveguard",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> AuthContext:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg], issuer="liveguard")
    except jwt.PyJWTError as exc:  # pragma: no cover - covered by integration tests
        raise ValueError(f"invalid token: {exc}") from exc
    return AuthContext(
        subject=str(claims["sub"]),
        tenant_id=str(claims["tid"]),
        role=Role(claims.get("role", Role.VIEWER.value)),
        scopes=tuple((claims.get("scope") or "").split()),
        kind="user",
    )
