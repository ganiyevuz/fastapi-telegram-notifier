from __future__ import annotations

from telegram_notifier.choices import Level, Severity, Status
from telegram_notifier.classify import classify_exception
from telegram_notifier.client import (
    notify_error_via_telegram,
    notify_error_via_telegram_sync,
)
from telegram_notifier.config import (
    TelegramNotifierSettings,
    configure,
    get_settings,
)
from telegram_notifier.message import (
    build_exception_message,
    build_traceback_content,
)
from telegram_notifier.middleware import TelegramExceptionMiddleware
from telegram_notifier.report import report_exception, set_on_log_created

__version__ = "0.1.0"


def __getattr__(name: str) -> type:
    if name == "ExceptionLog":
        try:
            from telegram_notifier.models import ExceptionLog
        except ImportError as e:
            msg = (
                "ExceptionLog requires sqlalchemy. "
                "Install with: pip install fastapi-telegram-notifier[db]"
            )
            raise ImportError(msg) from e

        globals()["ExceptionLog"] = ExceptionLog
        return ExceptionLog
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "Level",
    "Severity",
    "Status",
    "classify_exception",
    "notify_error_via_telegram",
    "notify_error_via_telegram_sync",
    "TelegramNotifierSettings",
    "configure",
    "get_settings",
    "build_exception_message",
    "build_traceback_content",
    "TelegramExceptionMiddleware",
    "report_exception",
    "set_on_log_created",
    "ExceptionLog",
]
