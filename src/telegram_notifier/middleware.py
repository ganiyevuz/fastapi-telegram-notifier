from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from telegram_notifier.report import report_exception


class TelegramExceptionMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that catches unhandled exceptions
    and reports them to Telegram."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            body = await request.body()
        except Exception:
            body = b""

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            await report_exception(
                exc, request=request, body=body
            )
            raise
