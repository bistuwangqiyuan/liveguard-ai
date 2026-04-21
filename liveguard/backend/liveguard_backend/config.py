"""
liveguard_backend.config
========================

12-Factor 配置 — 所有可变项走环境变量，机密禁止入源。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LVG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["dev", "staging", "prod"] = "dev"
    service_name: str = "liveguard-backend"
    instance_id: str = "local-0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True

    # --- HTTP ---
    http_host: str = "0.0.0.0"
    http_port: int = 8080
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    request_timeout_s: int = 30

    # --- Auth ---
    jwt_secret: str = "change-me-in-prod"
    jwt_alg: str = "HS256"
    jwt_ttl_s: int = 3600
    refresh_ttl_s: int = 7 * 24 * 3600
    api_key_header: str = "X-API-Key"

    # --- Persistence ---
    database_url: str = "sqlite+aiosqlite:///./liveguard_dev.db"
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # --- Kafka ---
    kafka_bootstrap: str = "localhost:9092"
    kafka_enabled: bool = False  # 单元测试/本地 demo 默认关闭
    topic_features: str = "streams.features.v1"
    topic_signals: str = "streams.signals.v1"
    topic_events: str = "streams.events.v1"
    topic_alerts: str = "alerts.v1"

    # --- Observability ---
    otel_endpoint: AnyHttpUrl | None = None
    prometheus_enabled: bool = True

    # --- Feature flags ---
    feature_privacy_mode_default: bool = True
    """默认启用隐私模式：边缘不上传原始视频/音频。"""
    feature_escalation_enabled: bool = True

    # --- Algorithm defaults ---
    algo_fsm_upper: float = 0.65
    algo_fsm_lower: float = 0.35
    algo_brief_to_long_s: float = 60.0
    algo_long_to_escalate_s: float = 120.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
