"""领域枚举。

统一源于 ``Requirements §2`` / ``Design §7 数据模型``。"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API = "api"


class StreamStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Severity(str, Enum):
    INFO = "INFO"
    P2 = "P2"
    P1 = "P1"
    P0 = "P0"


class AlertState(str, Enum):
    OPEN = "open"
    ACKED = "acked"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"
