from __future__ import annotations

import io
import logging
from datetime import UTC, datetime

import httpx

from telegram_notifier.config import get_settings

logger = logging.getLogger("telegram_notifier")

TELEGRAM_SEND_MESSAGE_URL = (
    "https://api.telegram.org/bot{token}/sendMessage"
)
TELEGRAM_SEND_DOCUMENT_URL = (
    "https://api.telegram.org/bot{token}/sendDocument"
)

CAPTION_MAX_LENGTH = 1024


async def notify_error_via_telegram(
    message: str,
    traceback_content: str | None = None,
) -> bool:
    """Send error notification to Telegram (async)."""
    settings = get_settings()
    token = settings.bot_token
    chat_ids = settings.chat_ids
    proxy = settings.proxy
    max_length = settings.message_max_length
    success = True

    for chat_id in chat_ids:
        try:
            if traceback_content:
                await _send_document_with_caption(
                    token,
                    chat_id,
                    message,
                    traceback_content,
                    proxy,
                )
            else:
                url = TELEGRAM_SEND_MESSAGE_URL.format(token=token)
                payload = {
                    "chat_id": chat_id,
                    "text": message[:max_length],
                    "parse_mode": "HTML",
                }
                await _async_post(url, data=payload, proxy=proxy)
            logger.info(
                "Telegram notification sent to %s", chat_id
            )
        except Exception as e:
            logger.error(
                "Telegram error for chat %s: %s", chat_id, e
            )
            success = False

    return success


def notify_error_via_telegram_sync(
    message: str,
    traceback_content: str | None = None,
) -> bool:
    """Send error notification to Telegram (sync fallback)."""
    settings = get_settings()
    token = settings.bot_token
    chat_ids = settings.chat_ids
    proxy = settings.proxy
    max_length = settings.message_max_length
    success = True

    for chat_id in chat_ids:
        try:
            if traceback_content:
                _send_document_with_caption_sync(
                    token,
                    chat_id,
                    message,
                    traceback_content,
                    proxy,
                )
            else:
                url = TELEGRAM_SEND_MESSAGE_URL.format(token=token)
                payload = {
                    "chat_id": chat_id,
                    "text": message[:max_length],
                    "parse_mode": "HTML",
                }
                _sync_post(url, data=payload, proxy=proxy)
            logger.info(
                "Telegram notification sent to %s", chat_id
            )
        except Exception as e:
            logger.error(
                "Telegram error for chat %s: %s", chat_id, e
            )
            success = False

    return success


async def _send_document_with_caption(
    token: str,
    chat_id: str,
    message: str,
    traceback_content: str,
    proxy: str | None,
) -> None:
    timestamp = datetime.now(tz=UTC).strftime(
        "%Y%m%d_%H%M%S"
    )
    last_line = traceback_content.strip().splitlines()[-1]
    exc_class = last_line.split(":")[0].split(".")[-1]
    filename = f"traceback_{exc_class}_{timestamp}.py"

    file_bytes = io.BytesIO(traceback_content.encode("utf-8"))
    url = TELEGRAM_SEND_DOCUMENT_URL.format(token=token)
    data = {
        "chat_id": chat_id,
        "caption": message[:CAPTION_MAX_LENGTH],
        "parse_mode": "HTML",
    }
    files = {"document": (filename, file_bytes, "text/x-python")}
    await _async_post(url, data=data, files=files, proxy=proxy)


def _send_document_with_caption_sync(
    token: str,
    chat_id: str,
    message: str,
    traceback_content: str,
    proxy: str | None,
) -> None:
    timestamp = datetime.now(tz=UTC).strftime(
        "%Y%m%d_%H%M%S"
    )
    last_line = traceback_content.strip().splitlines()[-1]
    exc_class = last_line.split(":")[0].split(".")[-1]
    filename = f"traceback_{exc_class}_{timestamp}.py"

    file_bytes = io.BytesIO(traceback_content.encode("utf-8"))
    url = TELEGRAM_SEND_DOCUMENT_URL.format(token=token)
    data = {
        "chat_id": chat_id,
        "caption": message[:CAPTION_MAX_LENGTH],
        "parse_mode": "HTML",
    }
    files = {"document": (filename, file_bytes, "text/x-python")}
    _sync_post(url, data=data, files=files, proxy=proxy)


async def _async_post(
    url: str,
    *,
    data: dict[str, str],
    files: dict[str, tuple[str, io.BytesIO, str]] | None = None,
    proxy: str | None = None,
) -> None:
    async with httpx.AsyncClient(proxy=proxy) as client:
        response = await client.post(
            url, data=data, files=files, timeout=3
        )
    response.raise_for_status()


def _sync_post(
    url: str,
    *,
    data: dict[str, str],
    files: dict[str, tuple[str, io.BytesIO, str]] | None = None,
    proxy: str | None = None,
) -> None:
    if proxy:
        with httpx.Client(proxy=proxy) as client:
            response = client.post(
                url, data=data, files=files, timeout=3
            )
    else:
        response = httpx.post(
            url, data=data, files=files, timeout=3
        )
    response.raise_for_status()
