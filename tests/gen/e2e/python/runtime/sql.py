from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement.removesuffix(";").strip())
            current = []
    remainder = "\n".join(current).strip()
    if remainder:
        statements.append(remainder.removesuffix(";").strip())
    return [statement for statement in statements if statement]


def apply_sql_file_sqlite(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text(encoding="utf-8"))
    conn.commit()


def apply_sql_file_postgres(conn, path: Path) -> None:
    for statement in split_sql_statements(path.read_text(encoding="utf-8")):
        conn.execute(statement)
    conn.commit()


def apply_sql_file_mysql(conn, path: Path) -> None:
    cur = conn.cursor()
    try:
        for statement in split_sql_statements(path.read_text(encoding="utf-8")):
            cur.execute(statement)
        conn.commit()
    finally:
        cur.close()


def apply_sql_file_duckdb(conn, path: Path) -> None:
    conn.execute(path.read_text(encoding="utf-8"))


def apply_sql_file_clickhouse(conn, path: Path) -> None:
    for statement in split_sql_statements(path.read_text(encoding="utf-8")):
        with closing(conn.cursor()) as cur:
            cur.execute(statement)


def apply_schema(
    engine: str,
    conn,
    schema_path: Path,
    before_path: Path | None,
) -> None:
    if engine == "sqlite":
        apply_sql_file_sqlite(conn, schema_path)
        if before_path is not None:
            apply_sql_file_sqlite(conn, before_path)
        return

    if engine == "postgres":
        apply_sql_file_postgres(conn, schema_path)
        if before_path is not None:
            apply_sql_file_postgres(conn, before_path)
        return

    if engine == "mysql":
        apply_sql_file_mysql(conn, schema_path)
        if before_path is not None:
            apply_sql_file_mysql(conn, before_path)
        return

    if engine == "duckdb":
        apply_sql_file_duckdb(conn, schema_path)
        if before_path is not None:
            apply_sql_file_duckdb(conn, before_path)
        return

    if engine == "clickhouse":
        apply_sql_file_clickhouse(conn, schema_path)
        if before_path is not None:
            apply_sql_file_clickhouse(conn, before_path)
        return

    msg = f"Unsupported engine: {engine}"
    raise AssertionError(msg)
