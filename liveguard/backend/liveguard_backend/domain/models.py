"""领域模型 — Pydantic dataclass 风格。

这些类型同时用于：
1. 服务内部业务逻辑（独立于 ORM）
2. 仓储层 ORM ↔ 领域 的显式映射
3. API 层 DTO 的父类（通过 ``model_dump`` / ``model_validate``）
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .enums import AlertState, Role, Severity, StreamStatus


def _now() -> datetime:
    return datetime.now(UTC)


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Tenant(_Base):
    id: str
    name: str
    plan: str = "starter"  # starter|pro|enterprise
    dpa_signed_at: datetime | None = None
    privacy_mode: bool = True
    region: str = "cn-east-1"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class User(_Base):
    id: str
    tenant_id: str
    email: EmailStr
    hashed_password: str | None = None
    display_name: str = ""
    role: Role = Role.VIEWER
    is_active: bool = True
    mfa_enrolled: bool = False
    created_at: datetime = Field(default_factory=_now)


class Host(_Base):
    """主播档案。"""
    id: str
    tenant_id: str
    display_name: str
    external_id: str | None = None  # 抖音/快手外部 ID
    face_vector_version: str = "face.arcface_mbf@r100-int8-v1.2-mock"
    voice_vector_version: str = "audio.ecapa_tdnn@ecapa-tdnn-c512-mock"
    consent_signed_at: datetime | None = None
    face_enrolled_at: datetime | None = None
    voice_enrolled_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class Stream(_Base):
    id: str
    tenant_id: str
    host_id: str | None = None
    platform: str = "custom"  # douyin|kuaishou|taobao|wechat|custom
    rtmp_url: str | None = None
    status: StreamStatus = StreamStatus.INACTIVE
    schedule_cron: str | None = None
    last_state: str = "IDLE"
    last_fusion_score: float = 0.0
    last_heartbeat_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class EventRecord(_Base):
    id: str
    tenant_id: str
    stream_id: str
    host_id: str | None = None
    event_type: str  # e.g. lvg.alert.host_offline.v1
    from_state: str
    to_state: str
    fusion_score: float
    severity: Severity
    signal_breakdown: dict[str, float] = Field(default_factory=dict)
    weights_used: dict[str, float] = Field(default_factory=dict)
    duration_offline_s: float = 0.0
    extras: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Alert(_Base):
    id: str
    tenant_id: str
    stream_id: str
    host_id: str | None = None
    severity: Severity
    state: AlertState = AlertState.OPEN
    event_ids: list[str] = Field(default_factory=list)
    title: str
    summary: str
    first_seen_at: datetime = Field(default_factory=_now)
    ack_by: str | None = None
    ack_at: datetime | None = None
    resolved_at: datetime | None = None
    evidence_uri: str | None = None
    created_at: datetime = Field(default_factory=_now)


class SignalIngest(_Base):
    """边缘上行的信号包 — 6 路数值 + 元数据。"""
    stream_id: str
    ts_ms: int
    face: float = 0.0
    person: float = 0.0
    reid: float = 0.0
    liveness: float = 0.0
    action: float = 0.0
    audio: float = 0.0
    deepfake: float = 0.0
    reid_similarity: float = 1.0
    temporal_var: float = 0.5
    screen_replay: float = 0.0
    edge_agent_id: str | None = None
    model_versions: dict[str, str] = Field(default_factory=dict)
