from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from telegram_notifier.client import (
    TELEGRAM_SEND_DOCUMENT_URL,
    TELEGRAM_SEND_MESSAGE_URL,
    notify_error_via_telegram,
    notify_error_via_telegram_sync,
)
from telegram_notifier.config import (
    TelegramNotifierSettings,
    configure,
)


class TestNotifyErrorAsync:
    async def test_sends_message_to_all_chat_ids(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111", "222"],
            )
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch(
            "telegram_notifier.client.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_cls.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            result = await notify_error_via_telegram("test msg")

        assert result is True
        assert mock_client.post.call_count == 2

    async def test_sends_document_when_traceback_provided(
        self,
    ) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
            )
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch(
            "telegram_notifier.client.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_cls.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            result = await notify_error_via_telegram(
                "msg",
                traceback_content="Traceback...\nValueError: x",
            )

        assert result is True
        call_args = mock_client.post.call_args
        expected_url = TELEGRAM_SEND_DOCUMENT_URL.format(
            token="tok"
        )
        assert call_args[0][0] == expected_url

    async def test_returns_false_on_error(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
            )
        )

        with patch(
            "telegram_notifier.client.httpx.AsyncClient"
        ) as mock_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("fail")
            mock_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_cls.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            result = await notify_error_via_telegram("msg")

        assert result is False


class TestNotifyErrorSync:
    def test_sends_message_sync(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
            )
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch(
            "telegram_notifier.client.httpx.post",
            return_value=mock_response,
        ) as mock_post:
            result = notify_error_via_telegram_sync("test msg")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        expected_url = TELEGRAM_SEND_MESSAGE_URL.format(
            token="tok"
        )
        assert call_kwargs[0][0] == expected_url

    def test_sends_document_sync(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
            )
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch(
            "telegram_notifier.client.httpx.post",
            return_value=mock_response,
        ) as mock_post:
            result = notify_error_via_telegram_sync(
                "msg",
                traceback_content="Traceback...\nValueError: x",
            )

        assert result is True
        call_kwargs = mock_post.call_args
        expected_url = TELEGRAM_SEND_DOCUMENT_URL.format(
            token="tok"
        )
        assert call_kwargs[0][0] == expected_url

    def test_returns_false_on_error_sync(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
            )
        )

        with patch(
            "telegram_notifier.client.httpx.post",
            side_effect=Exception("fail"),
        ):
            result = notify_error_via_telegram_sync("msg")

        assert result is False

    def test_uses_proxy_sync(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["111"],
                proxy="socks5://127.0.0.1:1080",
            )
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        with patch(
            "telegram_notifier.client.httpx.Client"
        ) as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_cls.return_value.__exit__ = MagicMock(
                return_value=False
            )

            result = notify_error_via_telegram_sync("msg")

        assert result is True
