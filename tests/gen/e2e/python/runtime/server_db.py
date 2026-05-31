from __future__ import annotations

import uuid
from urllib.parse import urlparse, urlunparse

import pytest

from .db import clickhouse_connect, mysql_connect
from .env import ensure_runtime_env, runtime_admin_url


def require_admin_url(engine: str) -> str:
    ensure_runtime_env()
    url = runtime_admin_url(engine)
    if not url:
        pytest.skip(
            f"No runtime database URL for {engine} "
            f"(set {engine.upper()}_* vars in .env or the environment)"
        )
    return url


def create_server_database(engine: str, admin_url: str) -> tuple[str, str]:
    db_name = _ephemeral_db_name()
    try:
        return _create_server_database_impl(engine, admin_url, db_name)
    except Exception as exc:
        pytest.skip(f"Cannot connect to {engine} at {admin_url}: {exc}")


def drop_server_database(engine: str, admin_url: str, db_name: str) -> None:
    if engine == "postgres":
        import psycopg

        with psycopg.connect(admin_url, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
        return

    if engine == "mysql":
        conn = mysql_connect(admin_url)
        try:
            cur = conn.cursor()
            cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return

    if engine == "clickhouse":
        client = _clickhouse_admin_client(urlparse(admin_url))
        client.execute(f"DROP DATABASE IF EXISTS {db_name}")


def open_setup_connection(engine: str, database_url: str):
    if engine == "postgres":
        import psycopg

        return psycopg.connect(database_url)

    if engine == "mysql":
        return mysql_connect(database_url)

    if engine == "clickhouse":
        return clickhouse_connect(database_url)

    msg = f"No setup connection for engine: {engine}"
    raise AssertionError(msg)


def _ephemeral_db_name() -> str:
    return f"norm_e2e_{uuid.uuid4().hex}"


def _case_database_url(admin_url: str, db_name: str) -> str:
    parsed = urlparse(admin_url)
    return urlunparse(parsed._replace(path=f"/{db_name}"))


def _clickhouse_admin_client(parsed):
    from clickhouse_driver import Client

    return Client(
        host=parsed.hostname or "localhost",
        port=parsed.port or 9000,
        user=parsed.username or "default",
        password=parsed.password or "",
        database=parsed.path.strip("/") or "default",
    )


def _create_server_database_impl(
    engine: str, admin_url: str, db_name: str
) -> tuple[str, str]:
    if engine == "postgres":
        import psycopg

        with psycopg.connect(admin_url, autocommit=True) as conn:
            conn.execute(f'CREATE DATABASE "{db_name}"')
        return _case_database_url(admin_url, db_name), db_name

    if engine == "mysql":
        conn = mysql_connect(admin_url)
        try:
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE `{db_name}`")
            conn.commit()
            cur.close()
        finally:
            conn.close()
        return _case_database_url(admin_url, db_name), db_name

    if engine == "clickhouse":
        parsed = urlparse(admin_url)
        client = _clickhouse_admin_client(parsed)
        client.execute(f"CREATE DATABASE {db_name}")
        return _case_database_url(admin_url, db_name), db_name

    msg = f"Unsupported server engine: {engine}"
    raise AssertionError(msg)
