from __future__ import annotations

import inspect
import os
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .db import clickhouse_connect, mysql_connect

CASE_DIR_ENV = "NORM_E2E_CASE_DIR"
ENGINE_ENV = "NORM_E2E_ENGINE"
ASYNC_ENV = "NORM_E2E_ASYNC"
DATABASE_URL_ENV = "NORM_E2E_DATABASE_URL"
SQLITE_PATH_ENV = "NORM_E2E_SQLITE_PATH"
DUCKDB_PATH_ENV = "NORM_E2E_DUCKDB_PATH"


def get_case_dir() -> Path:
    value = os.environ.get(CASE_DIR_ENV)
    if not value:
        msg = f"{CASE_DIR_ENV} is not set; runtime tests must be run via the harness."
        raise RuntimeError(msg)
    return Path(value)


def engine_name() -> str:
    value = os.environ.get(ENGINE_ENV)
    if not value:
        msg = f"{ENGINE_ENV} is not set; runtime tests must be run via the harness."
        raise RuntimeError(msg)
    return value


def open_sync_connection() -> Any:
    return _open_sync_connection(engine_name())


def close_sync_connection(conn: Any) -> None:
    conn.close()


async def open_connection() -> Any:
    return await _open_async_connection(engine_name())


async def close_connection(conn: Any) -> None:
    aexit = getattr(conn, "__aexit__", None)
    if aexit is not None:
        await aexit(None, None, None)
        return
    close = getattr(conn, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


def _open_sync_connection(engine: str) -> Any:
    if engine == "sqlite":
        path = os.environ.get(SQLITE_PATH_ENV)
        if not path:
            msg = f"{SQLITE_PATH_ENV} is not set."
            raise RuntimeError(msg)
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    if engine == "duckdb":
        path = os.environ.get(DUCKDB_PATH_ENV)
        if not path:
            msg = f"{DUCKDB_PATH_ENV} is not set."
            raise RuntimeError(msg)
        import duckdb

        return duckdb.connect(path)

    url = os.environ.get(DATABASE_URL_ENV)
    if not url:
        msg = f"{DATABASE_URL_ENV} is not set."
        raise RuntimeError(msg)

    if engine == "postgres":
        import psycopg

        return psycopg.connect(url)

    if engine == "mysql":
        return mysql_connect(url)

    if engine == "clickhouse":
        return clickhouse_connect(url)

    msg = f"Unsupported engine: {engine}"
    raise RuntimeError(msg)


async def _open_async_connection(engine: str) -> Any:
    if engine == "sqlite":
        path = os.environ.get(SQLITE_PATH_ENV)
        if not path:
            msg = f"{SQLITE_PATH_ENV} is not set."
            raise RuntimeError(msg)
        import aiosqlite

        conn = await aiosqlite.connect(path)
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn

    if engine == "duckdb":
        path = os.environ.get(DUCKDB_PATH_ENV)
        if not path:
            msg = f"{DUCKDB_PATH_ENV} is not set."
            raise RuntimeError(msg)
        import aioduck

        conn = aioduck.AsyncConnection(path)
        await conn.__aenter__()
        return conn

    url = os.environ.get(DATABASE_URL_ENV)
    if not url:
        msg = f"{DATABASE_URL_ENV} is not set."
        raise RuntimeError(msg)

    if engine == "postgres":
        import psycopg

        return await psycopg.AsyncConnection.connect(url)

    if engine == "mysql":
        import asyncmy

        parsed = urlparse(url)
        return await asyncmy.connect(
            host=parsed.hostname or "localhost",
            user=parsed.username or "root",
            password=parsed.password or "",
            db=parsed.path.lstrip("/"),
            port=parsed.port or 3306,
        )

    if engine == "clickhouse":
        from asynch import Connection

        parsed = urlparse(url)
        return Connection(
            host=parsed.hostname or "localhost",
            port=parsed.port or 9000,
            user=parsed.username or "default",
            password=parsed.password or "",
            database=parsed.path.lstrip("/") or "default",
        )

    msg = f"Unsupported engine: {engine}"
    raise RuntimeError(msg)
