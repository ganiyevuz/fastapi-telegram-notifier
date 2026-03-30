from __future__ import annotations

import logging
from collections.abc import Callable

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("telegram_notifier")


class TelegramNotifierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TN_")

    bot_token: str = ""
    chat_ids: list[str] = []
    environment: str | None = None
    proxy: str | None = None
    message_max_length: int = 4000
    ignore_exceptions: list[str] = []
    ignore_paths: list[str] = []
    store_exceptions: bool = False
    filter: Callable[..., bool] | None = None


_settings: TelegramNotifierSettings | None = None


def get_settings() -> TelegramNotifierSettings:
    global _settings
    if _settings is None:
        _settings = TelegramNotifierSettings()
    return _settings


def configure(settings: TelegramNotifierSettings) -> None:
    global _settings
    _settings = settings


def reset_settings() -> None:
    """Reset settings to None. Useful for testing."""
    global _settings
    _settings = None
