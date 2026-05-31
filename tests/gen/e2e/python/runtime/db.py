from __future__ import annotations

from urllib.parse import urlparse


def mysql_connect(url: str):
    import MySQLdb

    parsed = urlparse(url)
    return MySQLdb.connect(
        host=parsed.hostname or "localhost",
        user=parsed.username or "root",
        passwd=parsed.password or "",
        db=parsed.path.lstrip("/"),
        port=parsed.port or 3306,
    )


def clickhouse_connect(url: str):
    from clickhouse_driver.dbapi import connect

    parsed = urlparse(url)
    return connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 9000,
        user=parsed.username or "default",
        password=parsed.password or "",
        database=parsed.path.lstrip("/") or "default",
    )
