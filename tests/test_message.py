from __future__ import annotations

from starlette.requests import Request

from telegram_notifier.config import (
    TelegramNotifierSettings,
    configure,
)
from telegram_notifier.message import (
    _decode_body,
    build_exception_message,
    build_traceback_content,
)


def _make_request(
    path: str = "/test",
    method: str = "GET",
) -> Request:
    """Create a minimal mock Request."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)
    return request


class TestBuildTracebackContent:
    def test_returns_traceback_string(self) -> None:
        try:
            msg = "test error"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_traceback_content(exc)

        assert "ValueError" in result
        assert "test error" in result
        assert "Traceback" in result

    def test_format_includes_file_info(self) -> None:
        try:
            msg = "with file info"
            raise TypeError(msg)
        except TypeError as exc:
            result = build_traceback_content(exc)

        assert "test_message.py" in result


class TestBuildExceptionMessage:
    def test_basic_message_format(self) -> None:
        try:
            msg = "something broke"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(exc)

        assert "<b>ValueError</b>" in result
        assert "something broke" in result
        assert "<b>Message:</b>" in result
        assert "<b>Timestamp:</b>" in result

    def test_includes_environment(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                environment="production",
            )
        )
        try:
            msg = "env test"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(exc)

        assert "<b>production</b>" in result

    def test_includes_request_info(self) -> None:
        request = _make_request(
            path="/api/users", method="POST"
        )
        try:
            msg = "request test"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(
                exc, request=request
            )

        assert "/api/users" in result
        assert "POST" in result

    def test_includes_body(self) -> None:
        request = _make_request(path="/api/test", method="POST")
        body = b'{"name": "test"}'
        try:
            msg = "body test"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(
                exc, request=request, body=body
            )

        assert "test" in result

    def test_level_emoji(self) -> None:
        try:
            msg = "warning test"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(
                exc, level="warning"
            )

        assert "\U0001f7e1" in result

    def test_critical_emoji(self) -> None:
        try:
            msg = "critical"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(
                exc, level="critical"
            )

        assert "\u26d4" in result

    def test_truncates_to_max_length(self) -> None:
        configure(
            TelegramNotifierSettings(
                bot_token="tok",
                chat_ids=["1"],
                message_max_length=100,
            )
        )
        try:
            msg = "x" * 500
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(exc)

        assert len(result) <= 100

    def test_no_request_still_works(self) -> None:
        try:
            msg = "no request"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(exc)

        assert "ValueError" in result
        assert "Request" not in result

    def test_includes_traceback_preview(self) -> None:
        try:
            msg = "preview test"
            raise ValueError(msg)
        except ValueError as exc:
            result = build_exception_message(exc)

        assert "Traceback (preview)" in result
        assert "<pre>" in result


class TestDecodeBody:
    def test_none_body(self) -> None:
        assert _decode_body(None) == "{}"

    def test_empty_body(self) -> None:
        assert _decode_body(b"") == "{}"

    def test_valid_utf8(self) -> None:
        result = _decode_body(b'{"key": "value"}')
        assert "key" in result
        assert "value" in result

    def test_binary_data(self) -> None:
        result = _decode_body(b"\x80\x81\x82")
        assert result == "[binary data omitted]"

    def test_html_escaping(self) -> None:
        result = _decode_body(b"<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
