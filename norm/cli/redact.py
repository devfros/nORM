from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

_SENSITIVE_KEY_PATTERN = re.compile(r"(connection|url|dsn)", re.IGNORECASE)


def redact_url(url: str) -> str:
    if "://" not in url:
        return url
    parsed = urlparse(url)
    if parsed.password is None and parsed.username is None:
        return url
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    user = parsed.username or ""
    userinfo = f"{user}:***@" if user else "***@"
    netloc = f"{userinfo}{host}"
    return urlunparse(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def _redact_value(key: str, value: Any) -> Any:
    if isinstance(value, str) and _SENSITIVE_KEY_PATTERN.search(key):
        return redact_url(value)
    if isinstance(value, dict):
        return {
            item_key: _redact_value(item_key, item_value)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value


def redact_context(context: dict[str, object]) -> dict[str, object]:
    return {key: _redact_value(key, value) for key, value in context.items()}
