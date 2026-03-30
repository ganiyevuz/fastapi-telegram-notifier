from __future__ import annotations

import ipaddress

from starlette.requests import Request

SENSITIVE_HEADERS: frozenset[str] = frozenset({
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-csrftoken",
})


def get_client_ip(request: Request) -> str | None:
    """Extract client IP from request, checking X-Forwarded-For first."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",", 1)[0].strip()
        if _is_valid_ip(ip):
            return ip
        return None
    if request.client:
        return request.client.host
    return None


def _is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def get_filtered_headers(request: Request) -> dict[str, str]:
    """Return request headers with sensitive values filtered out."""
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        if key.lower() not in SENSITIVE_HEADERS:
            headers[key] = value
    return headers
