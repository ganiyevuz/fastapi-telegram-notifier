from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from telegram_notifier.config import (
    TelegramNotifierSettings,
    configure,
    reset_settings,
)
from telegram_notifier.middleware import TelegramExceptionMiddleware


@pytest.fixture(autouse=True)
def _reset_settings():
    """Reset settings before each test."""
    reset_settings()
    configure(
        TelegramNotifierSettings(
            bot_token="test-token",
            chat_ids=["123"],
        )
    )
    yield
    reset_settings()


def _create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TelegramExceptionMiddleware)

    @app.get("/ok")
    async def ok_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint() -> None:
        msg = "test error"
        raise ValueError(msg)

    @app.post("/body-error")
    async def body_error_endpoint(
        request: Request,
    ) -> None:
        msg = "body error"
        raise RuntimeError(msg)

    return app


@pytest.fixture()
def app() -> FastAPI:
    return _create_app()


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)
