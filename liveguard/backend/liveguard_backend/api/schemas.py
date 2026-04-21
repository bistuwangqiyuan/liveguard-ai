"""OpenAPI DTO — Pydantic v2。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from ..domain.enums import AlertState, Role, Severity, StreamStatus


class HealthStatus(BaseModel):
    service: str
    version: str
    status: str = "ok"
    timestamp: datetime
    checks: dict[str, str] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


class TenantCreateRequest(BaseModel):
    id: str
    name: str
    plan: str = "starter"
    region: str = "cn-east-1"


class TenantRead(BaseModel):
    id: str
    name: str
    plan: str
    region: str
    privacy_mode: bool
    created_at: datetime


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""
    role: Role = Role.VIEWER


class UserRead(BaseModel):
    id: str
    tenant_id: str
    email: EmailStr
    display_name: str
    role: Role
    is_active: bool


class HostCreateRequest(BaseModel):
    display_name: str
    external_id: str | None = None


class HostRead(BaseModel):
    id: str
    tenant_id: str
    display_name: str
    external_id: str | None = None
    face_enrolled_at: datetime | None = None
    voice_enrolled_at: datetime | None = None
    created_at: datetime


class StreamCreateRequest(BaseModel):
    platform: str = "custom"
    rtmp_url: str | None = None
    host_id: str | None = None
    schedule_cron: str | None = None


class StreamRead(BaseModel):
    id: str
    tenant_id: str
    host_id: str | None
    platform: str
    rtmp_url: str | None
    status: StreamStatus
    last_state: str
    last_fusion_score: float
    last_heartbeat_at: datetime | None


class SignalIngestRequest(BaseModel):
    stream_id: str
    ts_ms: int
    face: float = Field(0.0, ge=0.0, le=1.0)
    person: float = Field(0.0, ge=0.0, le=1.0)
    reid: float = Field(0.0, ge=0.0, le=1.0)
    liveness: float = Field(0.0, ge=0.0, le=1.0)
    action: float = Field(0.0, ge=0.0, le=1.0)
    audio: float = Field(0.0, ge=0.0, le=1.0)
    deepfake: float = Field(0.0, ge=0.0, le=1.0)
    reid_similarity: float = Field(1.0, ge=0.0, le=1.0)
    temporal_var: float = Field(0.5, ge=0.0)
    screen_replay: float = Field(0.0, ge=0.0, le=1.0)
    edge_agent_id: str | None = None
    model_versions: dict[str, str] = Field(default_factory=dict)


class IngestAck(BaseModel):
    stream_id: str
    state: str
    fusion_score: float
    offline_seconds: float
    state_event: dict[str, Any] | None = None
    cheat_flags: list[dict[str, Any]] = Field(default_factory=list)


class EventRead(BaseModel):
    id: str
    tenant_id: str
    stream_id: str
    event_type: str
    from_state: str
    to_state: str
    fusion_score: float
    severity: Severity
    duration_offline_s: float
    signal_breakdown: dict[str, float]
    weights_used: dict[str, float]
    created_at: datetime


class AlertRead(BaseModel):
    id: str
    tenant_id: str
    stream_id: str
    host_id: str | None
    severity: Severity
    state: AlertState
    event_ids: list[str]
    title: str
    summary: str
    first_seen_at: datetime
    ack_by: str | None
    ack_at: datetime | None
    resolved_at: datetime | None


class AlertAckRequest(BaseModel):
    note: str | None = None


class ApiError(BaseModel):
    error: str
    message: str
    request_id: str | None = None
