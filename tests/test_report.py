from __future__ import annotations

from unittest.mock import MagicMock, patch

from starlette.requests import Request

from telegram_notifier.config import (
    TelegramNotifierSettings,
    configure,
)
from telegram_notifier.report import (
    _extract_request_data,
    _should_report,
    report_exception,
)


def _closing_create_task(coro):
    """Mock create_task that closes the coroutine to avoid warnings."""
    coro.close()
    return MagicMock()


def _make_request(
    path: str = "/test",
    method: str = "GET",
    headers: list[tuple[bytes, bytes]] | None = None,
    client: tuple[str, int] | None = ("127.0.0.1", 8000),
    query_string: bytes = b"",
) -> Request:
    scope: dict = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query_string,
        "headers": headers or [],
    }
    if client:
        scope["client"] = client
    return Request(scope)


class TestShouldReport:
    def test_reports_by_default(self) -> None:
        assert _should_report(ValueError("x"), None) is True

    def test_ignores_exception_by_name(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                ignore_exceptions=["ValueError"],
            )
        )
        assert (
            _should_report(ValueError("x"), None) is False
        )

    def test_ignores_exception_by_mro(self) -> None:
        """Subclass of ignored exception should be ignored."""
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                ignore_exceptions=["ConnectionError"],
            )
        )
        assert (
            _should_report(
                ConnectionRefusedError("x"), None
            )
            is False
        )

    def test_ignores_path(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                ignore_paths=["/health"],
            )
        )
        request = _make_request(path="/health/check")
        assert (
            _should_report(ValueError("x"), request)
            is False
        )

    def test_does_not_ignore_non_matching_path(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                ignore_paths=["/health"],
            )
        )
        request = _make_request(path="/api/test")
        assert (
            _should_report(ValueError("x"), request) is True
        )

    def test_custom_filter(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                filter=lambda exc, req: False,
            )
        )
        assert (
            _should_report(ValueError("x"), None) is False
        )

    def test_custom_filter_allows(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                filter=lambda exc, req: True,
            )
        )
        assert (
            _should_report(ValueError("x"), None) is True
        )


class TestExtractRequestData:
    def test_returns_none_without_request(self) -> None:
        assert _extract_request_data(None, None) is None

    def test_extracts_path_and_method(self) -> None:
        request = _make_request(
            path="/api/test", method="POST"
        )
        data = _extract_request_data(request, None)
        assert data is not None
        assert data["path"] == "/api/test"
        assert data["method"] == "POST"

    def test_extracts_body(self) -> None:
        request = _make_request()
        data = _extract_request_data(
            request, b'{"key": "val"}'
        )
        assert data is not None
        assert data["body"] == '{"key": "val"}'

    def test_extracts_ip(self) -> None:
        request = _make_request(
            client=("10.0.0.1", 8000)
        )
        data = _extract_request_data(request, None)
        assert data is not None
        assert data["ip_address"] == "10.0.0.1"

    def test_extracts_query_params(self) -> None:
        request = _make_request(query_string=b"q=hello")
        data = _extract_request_data(request, None)
        assert data is not None
        assert data["query_params"] == {"q": "hello"}

    def test_binary_body_handled(self) -> None:
        request = _make_request()
        data = _extract_request_data(
            request, b"\x80\x81"
        )
        assert data is not None
        assert data["body"] == "[binary data]"


class TestReportException:
    async def test_report_returns_true(self) -> None:
        with patch(
            "telegram_notifier.report.asyncio.create_task",
            side_effect=_closing_create_task,
        ):
            result = await report_exception(
                ValueError("test")
            )

        assert result is True

    async def test_report_filtered_returns_false(
        self,
    ) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                ignore_exceptions=["ValueError"],
            )
        )

        result = await report_exception(
            ValueError("test")
        )
        assert result is False

    async def test_report_creates_task(self) -> None:
        with patch(
            "telegram_notifier.report.asyncio.create_task",
            side_effect=_closing_create_task,
        ) as mock_task:
            await report_exception(ValueError("test"))

        mock_task.assert_called_once()

    async def test_report_with_request(self) -> None:
        request = _make_request(
            path="/api/test", method="POST"
        )
        with patch(
            "telegram_notifier.report.asyncio.create_task",
            side_effect=_closing_create_task,
        ):
            result = await report_exception(
                ValueError("test"),
                request=request,
                body=b'{"key": "value"}',
            )

        assert result is True

    async def test_report_with_custom_level(self) -> None:
        with patch(
            "telegram_notifier.report.asyncio.create_task",
            side_effect=_closing_create_task,
        ) as mock_task:
            await report_exception(
                ValueError("test"),
                level="critical",
                severity="high",
            )

        mock_task.assert_called_once()
