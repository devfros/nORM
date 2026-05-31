from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from norm.config import load_norm_config

from .connections import (
    ASYNC_ENV,
    CASE_DIR_ENV,
    DATABASE_URL_ENV,
    DUCKDB_PATH_ENV,
    ENGINE_ENV,
    SQLITE_PATH_ENV,
)
from .env import project_root
from .server_db import (
    create_server_database,
    drop_server_database,
    open_setup_connection,
    require_admin_url,
)
from .sql import apply_schema

_PROJECT_ROOT = project_root()

_FILE_ENGINES = frozenset({"sqlite", "duckdb"})
_SERVER_ENGINES = frozenset({"postgres", "mysql", "clickhouse"})


def _runtime_env(
    case_dir: Path,
    *,
    engine: str,
    asynchronous: bool,
    db_path: Path | None = None,
    database_url: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    env[CASE_DIR_ENV] = str(case_dir)
    env[ENGINE_ENV] = engine
    env[ASYNC_ENV] = "1" if asynchronous else "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if db_path is not None:
        if engine == "sqlite":
            env[SQLITE_PATH_ENV] = str(db_path)
        else:
            env[DUCKDB_PATH_ENV] = str(db_path)
    if database_url is not None:
        env[DATABASE_URL_ENV] = database_url

    pythonpath_parts = [str(case_dir), str(_PROJECT_ROOT)]
    existing = env.get("PYTHONPATH")
    if existing:
        pythonpath_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


def _run_runtime_script(
    case_dir: Path,
    runtime_path: Path,
    *,
    case_name: str,
    env: dict[str, str],
) -> None:
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(runtime_path)],
        cwd=case_dir,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Case '{case_name}' runtime_test.py exited with {result.returncode}."
        )


def run_runtime_case(case_dir: Path, *, case_name: str) -> None:
    case_dir = case_dir.resolve()
    config = load_norm_config(case_dir / "norm.yaml")
    if not config.targets:
        raise AssertionError(f"Case '{case_name}' has no targets.")

    target = next(iter(config.targets.values()))
    if target.gen.python is None:
        raise AssertionError(f"Case '{case_name}' has no python gen config.")

    engine = target.sql.engine
    asynchronous = target.gen.python.asynchronous
    schema_path = (case_dir / target.sql.db_schema).resolve()
    before_path = case_dir / "runtime" / "before.sql"
    runtime_path = case_dir / "runtime" / "runtime_test.py"
    if not runtime_path.is_file():
        raise AssertionError(f"Case '{case_name}' has no runtime/runtime_test.py.")

    optional_before = before_path if before_path.is_file() else None

    if engine in _SERVER_ENGINES:
        admin_url = require_admin_url(engine)
        database_url, db_name = create_server_database(engine, admin_url)
        conn = open_setup_connection(engine, database_url)
        try:
            apply_schema(engine, conn, schema_path, optional_before)
        finally:
            conn.close()

        try:
            _run_runtime_script(
                case_dir,
                runtime_path,
                case_name=case_name,
                env=_runtime_env(
                    case_dir,
                    engine=engine,
                    asynchronous=asynchronous,
                    database_url=database_url,
                ),
            )
        finally:
            drop_server_database(engine, admin_url, db_name)
        return

    if engine not in _FILE_ENGINES:
        raise AssertionError(f"Unsupported engine '{engine}' for case '{case_name}'.")

    suffix = ".sqlite3" if engine == "sqlite" else ".duckdb"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as db_file:
        db_path = Path(db_file.name)

    try:
        if engine == "sqlite":
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                apply_schema(engine, conn, schema_path, optional_before)
            finally:
                conn.close()
        else:
            import duckdb

            db_path.unlink(missing_ok=True)
            conn = duckdb.connect(str(db_path))
            try:
                apply_schema(engine, conn, schema_path, optional_before)
            finally:
                conn.close()

        _run_runtime_script(
            case_dir,
            runtime_path,
            case_name=case_name,
            env=_runtime_env(
                case_dir,
                engine=engine,
                asynchronous=asynchronous,
                db_path=db_path,
            ),
        )
    finally:
        db_path.unlink(missing_ok=True)
