from __future__ import annotations

import asyncio
import logging
import socket

from starlette.requests import Request

from telegram_notifier.classify import classify_exception
from telegram_notifier.client import notify_error_via_telegram
from telegram_notifier.config import get_settings
from telegram_notifier.message import (
    build_exception_message,
    build_traceback_content,
)
from telegram_notifier.utils import (
    get_client_ip,
    get_filtered_headers,
)

logger = logging.getLogger("telegram_notifier")


def _should_report(
    exc: BaseException,
    request: Request | None,
) -> bool:
    """Check ignore rules. Returns False if skipped."""
    settings = get_settings()

    ignore_classes = settings.ignore_exceptions
    if ignore_classes:
        exc_names = {cls.__name__ for cls in type(exc).__mro__}
        if exc_names & set(ignore_classes):
            return False

    ignore_paths = settings.ignore_paths
    if ignore_paths and request and hasattr(request, "url"):
        path = str(request.url.path)
        for prefix in ignore_paths:
            if path.startswith(prefix):
                return False

    custom_filter = settings.filter
    if custom_filter is not None:
        return bool(custom_filter(exc, request))

    return True


def _extract_request_data(
    request: Request | None,
    body: bytes | None,
) -> dict[str, str | dict] | None:
    """Extract serializable request data from the request."""
    if not request or not hasattr(request, "url"):
        return None

    body_str = ""
    if body:
        try:
            body_str = body.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            body_str = "[binary data]"

    user_info = ""
    try:
        user = getattr(request.state, "user", None)
        if user is not None:
            user_info = str(user)
    except Exception:
        pass

    query_params = dict(request.query_params)

    return {
        "path": str(request.url.path),
        "method": request.method,
        "query_params": query_params,
        "body": body_str,
        "user_info": user_info,
        "ip_address": get_client_ip(request) or "",
        "headers": get_filtered_headers(request),
    }


async def _do_report(
    exc_class_name: str,
    exc_message: str,
    message: str,
    traceback_content: str,
    effective_level: str,
    effective_severity: str,
    request_data: dict[str, str | dict] | None,
) -> None:
    """Actual reporting work -- runs as an asyncio task."""
    try:
        sent = await notify_error_via_telegram(
            message, traceback_content=traceback_content
        )
    except Exception as e:
        logger.error(
            "telegram_notifier: failed to send: %s", e
        )
        sent = False

    settings = get_settings()
    if settings.store_exceptions:
        try:

            from telegram_notifier.models import ExceptionLog

            # Users must set up engine/session themselves;
            # we import from a well-known location
            log_entry = ExceptionLog(
                exception_class=exc_class_name,
                message=exc_message,
                traceback=traceback_content,
                level=effective_level,
                severity=effective_severity,
                is_sent=sent,
                hostname=socket.gethostname(),
                environment=settings.environment or "",
            )
            if request_data:
                for key, value in request_data.items():
                    if hasattr(log_entry, key):
                        setattr(log_entry, key, value)

            logger.info(
                "telegram_notifier: ExceptionLog prepared "
                "(user must persist via their own session)"
            )
        except Exception as e:
            logger.error(
                "telegram_notifier: failed to store: %s", e
            )


async def report_exception(
    exc: BaseException,
    request: Request | None = None,
    body: bytes | None = None,
    level: str | None = None,
    severity: str | None = None,
) -> bool:
    """Report an exception to Telegram. Non-blocking (fire-and-forget).

    Returns True if reporting was initiated, False if filtered out.
    """
    if not _should_report(exc, request):
        logger.debug(
            "Skipped reporting %s (filtered)",
            type(exc).__name__,
        )
        return False

    auto_level, auto_severity = classify_exception(exc)
    effective_level = level or auto_level
    effective_severity = severity or auto_severity

    message = build_exception_message(
        exc,
        request=request,
        body=body,
        level=effective_level,
    )
    traceback_content = build_traceback_content(exc)
    request_data = _extract_request_data(request, body)

    asyncio.create_task(
        _do_report(
            exc_class_name=type(exc).__name__,
            exc_message=str(exc),
            message=message,
            traceback_content=traceback_content,
            effective_level=effective_level,
            effective_severity=effective_severity,
            request_data=request_data,
        )
    )

    return True
