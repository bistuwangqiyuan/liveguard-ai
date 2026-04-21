"""Pytest 共用夹具 — 用 sqlite:memory 和 InMemoryBus 做集成测试。"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("LVG_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LVG_JWT_SECRET", "unit-test-secret")
os.environ.setdefault("LVG_ENV", "dev")
os.environ.setdefault("LVG_LOG_JSON", "false")


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # 确保每个测试重新读环境变量
    from liveguard_backend import config

    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
