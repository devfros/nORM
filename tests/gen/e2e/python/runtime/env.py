from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
_ENV_LOADED = False
_DOTENV_VARS: dict[str, str] = {}


def project_root() -> Path:
    return _PROJECT_ROOT


def ensure_runtime_env() -> None:
    global _ENV_LOADED, _DOTENV_VARS
    if _ENV_LOADED:
        return
    _DOTENV_VARS = _read_dotenv(_PROJECT_ROOT / ".env")
    _ENV_LOADED = True


def runtime_admin_url(engine: str) -> str | None:
    ensure_runtime_env()
    if engine == "postgres":
        return _postgres_url()
    if engine == "mysql":
        return _mysql_url()
    if engine == "clickhouse":
        return _clickhouse_url()
    return None


def _resolve(name: str) -> str | None:
    if name in _DOTENV_VARS:
        return _DOTENV_VARS[name]
    return os.environ.get(name)


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _postgres_url() -> str | None:
    host = _resolve("POSTGRES_HOST")
    user = _resolve("POSTGRES_USER")
    password = _resolve("POSTGRES_PASSWORD")
    database = _resolve("POSTGRES_DB")
    if not host or not user or password is None or not database:
        return None
    port = _resolve("POSTGRES_PORT") or "5432"
    return _format_url("postgresql", user, password, host, port, database)


def _mysql_url() -> str | None:
    host = _resolve("MYSQL_HOST")
    user = _resolve("MYSQL_USER")
    password = _resolve("MYSQL_PASSWORD")
    database = _resolve("MYSQL_DATABASE")
    if not host or not user or password is None or not database:
        return None
    port = _resolve("MYSQL_PORT") or "3306"
    return _format_url("mysql", user, password, host, port, database)


def _clickhouse_url() -> str | None:
    host = _resolve("CLICKHOUSE_HOST")
    user = _resolve("CLICKHOUSE_USER")
    password = _resolve("CLICKHOUSE_PASSWORD")
    database = _resolve("CLICKHOUSE_DATABASE")
    if not host or not user or password is None or not database:
        return None
    port = _resolve("CLICKHOUSE_PORT") or "9000"
    return _format_url("clickhouse", user, password, host, port, database)


def _format_url(
    scheme: str,
    user: str,
    password: str,
    host: str,
    port: str,
    database: str,
) -> str:
    user_enc = quote(user, safe="")
    password_enc = quote(password, safe="")
    return f"{scheme}://{user_enc}:{password_enc}@{host}:{port}/{database}"
