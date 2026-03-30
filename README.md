# fastapi-telegram-notifier

[![PyPI version](https://img.shields.io/pypi/v/fastapi-telegram-notifier.svg)](https://pypi.org/project/fastapi-telegram-notifier/)
[![Python versions](https://img.shields.io/pypi/pyversions/fastapi-telegram-notifier.svg)](https://pypi.org/project/fastapi-telegram-notifier/)
[![FastAPI](https://img.shields.io/badge/fastapi-%3E%3D0.100-teal.svg)](https://pypi.org/project/fastapi-telegram-notifier/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/ganiyevuz/fastapi-telegram-notifier/blob/main/LICENSE)

Catch unhandled FastAPI exceptions and send formatted error reports to Telegram — like a lightweight Sentry. Includes full traceback as a `.py` file attachment with syntax highlighting, smart exception classification, async-first design, and optional SQLAlchemy logging.

---

## Features

- **Automatic exception catching** via Starlette middleware
- **Async-first** -- uses `httpx.AsyncClient` and `asyncio.create_task()` for non-blocking fire-and-forget
- **Smart exception classification** -- auto-assigns level and severity based on exception type (MRO-based)
- **Formatted Telegram messages** with emoji levels, request context, and traceback preview
- **Full traceback as `.py` file** -- Telegram renders Python syntax highlighting
- **Exception filtering** -- ignore specific exceptions, paths, or use custom filter functions
- **Optional SQLAlchemy model** -- store every exception with request details, severity, status
- **Pydantic Settings** -- configure via environment variables with `TN_` prefix
- **Sync fallback** -- `notify_error_via_telegram_sync()` for non-async contexts
- **Multi-chat support** -- send to multiple Telegram chats
- **Proxy support** for restricted environments
- **PEP 561 typed** -- ships with `py.typed` marker

---

## Quick Start

### 1. Install

```bash
pip install fastapi-telegram-notifier

# With optional SQLAlchemy support for database logging
pip install fastapi-telegram-notifier[db]
```

### 2. Get a Telegram Bot Token

1. Open Telegram, search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token (e.g. `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
4. Send a message to your bot, then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`

### 3. Configure

Set environment variables (all prefixed with `TN_`):

```bash
export TN_BOT_TOKEN="your-bot-token"
export TN_CHAT_IDS='["your-chat-id"]'
export TN_ENVIRONMENT="production"
```

Or configure programmatically:

```python
from telegram_notifier import TelegramNotifierSettings, configure

configure(TelegramNotifierSettings(
    bot_token="your-bot-token",
    chat_ids=["your-chat-id"],
    environment="production",
))
```

### 4. Add Middleware

```python
from fastapi import FastAPI
from telegram_notifier import TelegramExceptionMiddleware

app = FastAPI()
app.add_middleware(TelegramExceptionMiddleware)
```

That's it. Any unhandled exception will now send a notification to your Telegram chat.

---

## Settings

All settings can be configured via environment variables with the `TN_` prefix or passed to `TelegramNotifierSettings`:

| Setting | Env Variable | Type | Default | Description |
|---------|-------------|------|---------|-------------|
| `bot_token` | `TN_BOT_TOKEN` | `str` | **required** | Telegram Bot API token |
| `chat_ids` | `TN_CHAT_IDS` | `list[str]` | **required** | Telegram chat IDs to send notifications to |
| `environment` | `TN_ENVIRONMENT` | `str \| None` | `None` | Environment name shown in messages |
| `proxy` | `TN_PROXY` | `str \| None` | `None` | Proxy URL for Telegram API requests |
| `message_max_length` | `TN_MESSAGE_MAX_LENGTH` | `int` | `4000` | Maximum message length before truncation |
| `ignore_exceptions` | `TN_IGNORE_EXCEPTIONS` | `list[str]` | `[]` | Exception class names to skip (checks MRO) |
| `ignore_paths` | `TN_IGNORE_PATHS` | `list[str]` | `[]` | URL path prefixes to skip |
| `store_exceptions` | `TN_STORE_EXCEPTIONS` | `bool` | `False` | Enable SQLAlchemy logging |
| `filter` | -- | `callable` | `None` | Custom filter function (programmatic only) |

---

## Exception Filtering

Control which exceptions get reported with three layers of filtering:

### Ignore by exception class

```python
configure(TelegramNotifierSettings(
    bot_token="...",
    chat_ids=["..."],
    ignore_exceptions=[
        "HTTPException",
        "RequestValidationError",
        "WebSocketDisconnect",
    ],
))
```

This checks the exception's MRO, so `"ConnectionError"` also catches `ConnectionRefusedError`, `ConnectionResetError`, etc.

### Ignore by path

```python
configure(TelegramNotifierSettings(
    bot_token="...",
    chat_ids=["..."],
    ignore_paths=[
        "/health",
        "/favicon.ico",
        "/.well-known",
    ],
))
```

### Custom filter function

```python
configure(TelegramNotifierSettings(
    bot_token="...",
    chat_ids=["..."],
    filter=lambda exc, request: (
        not str(request.url.path).startswith("/admin/")
        if request else True
    ),
))
```

Return `True` to report, `False` to skip. Filters are evaluated in order: `ignore_exceptions` -> `ignore_paths` -> `filter`.

---

## Smart Exception Classification

Exceptions are automatically classified by level and severity based on their type:

| Category | Level | Severity | Examples |
|----------|-------|----------|----------|
| System failures | `critical` | `critical` | `MemoryError`, `RecursionError`, `SystemExit` |
| Infrastructure | `error` | `high` | `ConnectionError`, `TimeoutError`, `OSError` |
| Client/validation | `warning` | `low` | `HTTPException`, `RequestValidationError`, `WebSocketDisconnect` |
| Default (bugs) | `error` | `moderate` | `TypeError`, `KeyError`, `AttributeError` |

You can override auto-classification by passing explicit `level` and `severity` to `report_exception()`.

---

## Usage

### Middleware (recommended)

The middleware catches all unhandled exceptions automatically:

```python
from fastapi import FastAPI
from telegram_notifier import TelegramExceptionMiddleware

app = FastAPI()
app.add_middleware(TelegramExceptionMiddleware)
```

### Manual Reporting

Report exceptions programmatically:

```python
from telegram_notifier import report_exception

try:
    do_something()
except Exception as exc:
    await report_exception(exc, level="critical", severity="high")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exc` | `Exception` | **required** | The exception to report |
| `request` | `Request \| None` | `None` | Starlette request (adds path, method, body, user) |
| `body` | `bytes \| None` | `None` | Request body |
| `level` | `str \| None` | auto | Overrides auto-classification |
| `severity` | `str \| None` | auto | Overrides auto-classification |

### Sync Fallback

For non-async contexts (scripts, CLI tools, background jobs):

```python
from telegram_notifier import (
    build_exception_message,
    build_traceback_content,
    notify_error_via_telegram_sync,
)

try:
    do_something()
except Exception as exc:
    message = build_exception_message(exc)
    traceback_content = build_traceback_content(exc)
    notify_error_via_telegram_sync(message, traceback_content)
```

---

## Non-Blocking Design

All Telegram API calls run as fire-and-forget `asyncio.create_task()` -- your request response is never delayed by slow network or Telegram downtime. This is the async equivalent of the Django version's background thread approach.

---

## Telegram Message Format

Each notification is sent as a **document** (`.py` file with full traceback) with a **caption** containing:

```
🔴 ValueError in production

Message: invalid literal for int()
Timestamp: 2026-03-11 12:30:45

▸ Traceback (preview)
    value = int(user_input)
ValueError: invalid literal for int() with base 10: 'abc'

▸ Request
  Path: /api/users/
  Method: POST
  Body: {"name": "test"}
  User: admin@example.com
```

**Level emojis:** ⚪ debug | 🔵 info | 🟡 warning | 🔴 error | ⛔ critical

The attached `.py` file contains the **complete traceback** with Python syntax highlighting in Telegram.

---

## SQLAlchemy Logging (Optional)

Requires the `db` extra: `pip install fastapi-telegram-notifier[db]`

### Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from telegram_notifier import configure, set_on_log_created, TelegramNotifierSettings
from telegram_notifier.models import Base

engine = create_async_engine("postgresql+asyncpg://...")
async_session = async_sessionmaker(engine)

# 1. Create tables
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# 2. Enable storage in settings
configure(TelegramNotifierSettings(
    bot_token="...",
    chat_ids=["..."],
    store_exceptions=True,
))

# 3. Register a callback to persist log entries
async def persist_log(log_entry):
    async with async_session() as session:
        session.add(log_entry)
        await session.commit()

set_on_log_created(persist_log)
```

Without calling `set_on_log_created()`, logs are created but not persisted (a warning is logged). If SQLAlchemy is not installed, `store_exceptions=True` is silently ignored with an error log.

### ExceptionLog Fields

| Field | Type | Description |
|-------|------|-------------|
| `exception_class` | `String(255)` | e.g. `"ValueError"` |
| `message` | `Text` | Exception message |
| `traceback` | `Text` | Full traceback |
| `level` | `String(10)` | `debug`, `info`, `warning`, `error`, `critical` |
| `severity` | `String(10)` | `low`, `moderate`, `high`, `critical` |
| `status` | `String(10)` | `new`, `seen`, `resolved`, `ignored` |
| `path` | `String(500)` | Request path |
| `method` | `String(10)` | HTTP method |
| `query_params` | `JSON` | Query string parameters |
| `body` | `Text` | Request body |
| `user_info` | `String(255)` | User string |
| `ip_address` | `String(45)` | Client IP |
| `headers` | `JSON` | Request headers (sensitive filtered) |
| `hostname` | `String(255)` | Server hostname |
| `environment` | `String(50)` | Environment from settings |
| `is_sent` | `Boolean` | Whether Telegram notification was sent |
| `created_at` | `DateTime` | When the exception occurred |

---

## Public API

```python
from telegram_notifier import (
    # Core
    report_exception,                  # Report an exception (async, fire-and-forget)
    notify_error_via_telegram,         # Send message to Telegram (async)
    notify_error_via_telegram_sync,    # Send message to Telegram (sync)
    classify_exception,                # Get (level, severity) for an exception

    # Message building
    build_exception_message,           # Build formatted HTML message
    build_traceback_content,           # Get full traceback string

    # Middleware
    TelegramExceptionMiddleware,       # Starlette exception middleware

    # Configuration
    TelegramNotifierSettings,          # Pydantic settings model
    configure,                         # Set settings programmatically
    get_settings,                      # Get current settings

    # Database logging (requires `pip install fastapi-telegram-notifier[db]`)
    set_on_log_created,                # Register async callback to persist ExceptionLog
    ExceptionLog,                      # SQLAlchemy model (lazy-loaded)

    # Enums
    Level,                             # debug, info, warning, error, critical
    Severity,                          # low, moderate, high, critical
    Status,                            # new, seen, resolved, ignored
)
```

---

## Requirements

- Python >= 3.11
- FastAPI >= 0.100.0
- httpx >= 0.28.1
- pydantic-settings >= 2.0.0
- SQLAlchemy >= 2.0 (optional — install with `pip install fastapi-telegram-notifier[db]`)

---

## Development

```bash
git clone https://github.com/ganiyevuz/fastapi-telegram-notifier.git
cd fastapi-telegram-notifier

# Install dependencies
uv sync --group dev

# Copy env file and add your bot token
cp .env.example .env

# Run tests
pytest

# Run linter
ruff check .
```

---

## License

MIT