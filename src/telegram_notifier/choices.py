from __future__ import annotations

from enum import StrEnum


class Level(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Severity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Status(StrEnum):
    NEW = "new"
    SEEN = "seen"
    RESOLVED = "resolved"
    IGNORED = "ignored"
