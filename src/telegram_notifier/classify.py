from __future__ import annotations

from telegram_notifier.choices import Level, Severity

# Critical: system-level failures that need immediate attention
_CRITICAL_EXCEPTIONS: frozenset[str] = frozenset({
    "SystemExit",
    "MemoryError",
    "RecursionError",
    "SystemError",
})

# Warning: expected client/validation errors, not bugs
_WARNING_EXCEPTIONS: frozenset[str] = frozenset({
    "HTTPException",
    "RequestValidationError",
    "WebSocketDisconnect",
    "ValidationError",
    "StarletteHTTPException",
})

# High severity: infrastructure/data failures
_HIGH_SEVERITY_EXCEPTIONS: frozenset[str] = frozenset({
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "TimeoutError",
    "OSError",
    "IOError",
    "PermissionError",
    "FileNotFoundError",
    "DatabaseError",
    "OperationalError",
    "IntegrityError",
})


def classify_exception(
    exc: BaseException,
) -> tuple[str, str]:
    """Return (level, severity) for an exception.

    Walks the MRO so subclasses of known types are classified
    correctly (e.g. IntegrityError inherits DatabaseError).
    """
    names = {cls.__name__ for cls in type(exc).__mro__}

    if names & _CRITICAL_EXCEPTIONS:
        return Level.CRITICAL, Severity.CRITICAL

    if names & _WARNING_EXCEPTIONS:
        return Level.WARNING, Severity.LOW

    if names & _HIGH_SEVERITY_EXCEPTIONS:
        return Level.ERROR, Severity.HIGH

    return Level.ERROR, Severity.MODERATE
