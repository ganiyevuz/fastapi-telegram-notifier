from __future__ import annotations

import html
import traceback
from datetime import UTC, datetime

from starlette.requests import Request

from telegram_notifier.config import get_settings

TRACEBACK_PREVIEW_LINES = 5

LEVEL_EMOJI: dict[str, str] = {
    "debug": "\u26aa",
    "info": "\U0001f535",
    "warning": "\U0001f7e1",
    "error": "\U0001f534",
    "critical": "\u26d4",
}


def build_traceback_content(exc: BaseException) -> str:
    """Return the full traceback as a string."""
    return "".join(traceback.format_exception(exc))


def build_exception_message(
    exc: BaseException,
    request: Request | None = None,
    body: bytes | None = None,
    level: str = "error",
) -> str:
    """Build a formatted HTML message for Telegram."""
    settings = get_settings()
    timestamp = datetime.now(tz=UTC).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    tb_string = "".join(traceback.format_exception(exc))
    exc_class = html.escape(exc.__class__.__name__)
    exc_message = html.escape(str(exc))
    max_length = settings.message_max_length
    environment = settings.environment

    emoji = LEVEL_EMOJI.get(level, "\U0001f534")
    env_tag = (
        f" in <b>{html.escape(str(environment))}</b>"
        if environment
        else ""
    )

    parts = [
        f"{emoji} <b>{exc_class}</b>{env_tag}",
        "",
        f"<b>Message:</b> {exc_message}",
        f"<b>Timestamp:</b> <i>{timestamp}</i>",
    ]

    tb_lines = tb_string.strip().splitlines()
    preview_lines = tb_lines[-TRACEBACK_PREVIEW_LINES:]
    tb_preview = html.escape("\n".join(preview_lines))
    parts.append(
        f"\n\u25b8 <b>Traceback (preview)</b>\n<pre>{tb_preview}</pre>"
    )

    if request and hasattr(request, "url"):
        body_str = _decode_body(body)
        request_lines = [
            "\n\u25b8 <b>Request</b>",
            (
                "<blockquote>"
                f"<b>Path:</b> <code>"
                f"{html.escape(str(request.url.path))}</code>"
            ),
            (
                f"<b>Method:</b> <code>"
                f"{html.escape(request.method)}</code>"
            ),
        ]

        if body_str != "{}":
            request_lines.append(
                f"<b>Body:</b>\n<pre>{body_str}</pre>"
            )

        try:
            user = getattr(request.state, "user", None)
            if user is not None:
                request_lines.append(
                    "<b>User:</b> "
                    f"<code>{html.escape(str(user))}</code>",
                )
        except Exception:
            pass

        request_lines.append("</blockquote>")
        parts.extend(request_lines)

    return "\n".join(parts)[:max_length]


def _decode_body(body: bytes | None) -> str:
    if not body:
        return "{}"
    try:
        return html.escape(body.decode("utf-8"))
    except (UnicodeDecodeError, AttributeError):
        return "[binary data omitted]"
