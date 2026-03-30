from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestTelegramExceptionMiddleware:
    def test_successful_request_passes_through(
        self, client: TestClient
    ) -> None:
        response = client.get("/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_exception_triggers_report(
        self, client: TestClient
    ) -> None:
        with patch(
            "telegram_notifier.middleware.report_exception",
            new_callable=AsyncMock,
        ) as mock_report:
            response = client.get("/error")

        assert response.status_code == 500
        mock_report.assert_called_once()
        call_args = mock_report.call_args
        exc = call_args.kwargs.get(
            "exc"
        ) or call_args.args[0]
        assert isinstance(exc, ValueError)

    def test_exception_includes_request(
        self, client: TestClient
    ) -> None:
        with patch(
            "telegram_notifier.middleware.report_exception",
            new_callable=AsyncMock,
        ) as mock_report:
            client.get("/error")

        call_kwargs = mock_report.call_args.kwargs
        assert "request" in call_kwargs
        assert call_kwargs["request"] is not None

    def test_exception_includes_body(
        self, client: TestClient
    ) -> None:
        with patch(
            "telegram_notifier.middleware.report_exception",
            new_callable=AsyncMock,
        ) as mock_report:
            client.post(
                "/body-error",
                json={"key": "value"},
            )

        call_kwargs = mock_report.call_args.kwargs
        assert "body" in call_kwargs

    def test_exception_is_reraised(
        self, app: FastAPI
    ) -> None:
        """Middleware should re-raise the exception."""
        test_client = TestClient(
            app, raise_server_exceptions=False
        )
        with patch(
            "telegram_notifier.middleware.report_exception",
            new_callable=AsyncMock,
        ):
            response = test_client.get("/error")

        assert response.status_code == 500
