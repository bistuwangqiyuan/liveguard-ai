"""Notify 服务配置。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class NotifySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LVG_NOTIFY_", env_file=".env", extra="ignore")
    http_host: str = "0.0.0.0"
    http_port: int = 8081
    log_level: str = "INFO"
    kafka_bootstrap: str = "localhost:9092"
    kafka_enabled: bool = False
    topic_jobs: str = "notify.jobs.v1"
    max_inflight: int = 128


@lru_cache(maxsize=1)
def get_settings() -> NotifySettings:
    return NotifySettings()  # type: ignore[call-arg]
