"""结构化日志初始化（structlog + stdlib logging）。"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from .config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level, logging.INFO)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json:
        processors = shared + [structlog.processors.JSONRenderer(sort_keys=True)]
    else:
        processors = shared + [structlog.dev.ConsoleRenderer(colors=True)]

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=level, format="%(message)s", stream=sys.stdout, force=True)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()
