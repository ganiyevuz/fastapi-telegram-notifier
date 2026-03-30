"""Example FastAPI app with Telegram exception notifier.

Run:
    cp ../.env.example .env  # fill in your bot token and chat IDs
    uvicorn app:app --reload

Then visit:
    http://localhost:8000/         -> 200 OK
    http://localhost:8000/error    -> triggers ValueError, sends Telegram notification
    http://localhost:8000/timeout  -> triggers TimeoutError (high severity)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from telegram_notifier import (
    TelegramExceptionMiddleware,
    TelegramNotifierSettings,
    configure,
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure(
        TelegramNotifierSettings(
            # reads TN_BOT_TOKEN, TN_CHAT_IDS, etc. from env
            environment="example",
            ignore_paths=["/health"],
        )
    )
    yield


app = FastAPI(title="Telegram Notifier Example", lifespan=lifespan)
app.add_middleware(TelegramExceptionMiddleware)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    """This path is ignored by the notifier."""
    return {"status": "healthy"}


@app.get("/error")
async def trigger_error() -> None:
    msg = "This is a test exception for Telegram Notifier"
    raise ValueError(msg)


@app.get("/timeout")
async def trigger_timeout() -> None:
    msg = "Simulated connection timeout"
    raise TimeoutError(msg)


@app.post("/body-error")
async def trigger_body_error(data: dict) -> None:
    msg = "Error processing request body"
    raise RuntimeError(msg)
