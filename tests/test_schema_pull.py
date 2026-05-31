import pytest
from sqlglot import Dialects

from norm.cli.schema import (
    _ensure_postgres_engine,
    clean_schema_text,
    format_pulled_schema,
)
from norm.errors import NormError, NormErrorCode
from norm.schemas.config import GenConfig, SqlConfig, SqlMigrations, TargetConfig

PG_DUMP_FIXTURE = """
SET statement_timeout = 0;
SET lock_timeout = 0;
SELECT pg_catalog.set_config('search_path', '', false);
\\restrict secret

CREATE SCHEMA app;

CREATE TYPE app.mood AS ENUM (
    'sad',
    'ok'
);

CREATE TABLE app.users (
    id integer NOT NULL,
    mood app.mood NOT NULL
);

COMMENT ON TABLE app.users IS 'Application users';
""".strip()


def test_clean_schema_text_strips_pg_dump_noise() -> None:
    cleaned = clean_schema_text(PG_DUMP_FIXTURE)

    assert "SET statement_timeout" not in cleaned
    assert "pg_catalog.set_config" not in cleaned
    assert "\\restrict" not in cleaned
    assert "CREATE SCHEMA app" in cleaned
    assert "COMMENT ON TABLE app.users" in cleaned


def test_format_pulled_schema_parses_and_emits_all_statements() -> None:
    formatted = format_pulled_schema(PG_DUMP_FIXTURE, Dialects.POSTGRES)

    assert "CREATE SCHEMA" in formatted
    assert "CREATE TYPE" in formatted
    assert "CREATE TABLE" in formatted
    assert "COMMENT ON TABLE" in formatted
    assert formatted.count(";") >= 4


def test_format_pulled_schema_rejects_empty_input() -> None:
    with pytest.raises(NormError) as exc_info:
        format_pulled_schema("SET foo = bar;\n", Dialects.POSTGRES)

    assert exc_info.value.code == NormErrorCode.INVALID_CONFIG


def test_ensure_postgres_engine_rejects_non_postgres() -> None:
    target = TargetConfig(
        name="api",
        sql=SqlConfig(
            db_schema="./schema.sql",
            repositories="./repos",
            engine="sqlite",
            migrations=SqlMigrations(
                connection="postgresql://user:pass@localhost:5432/db"
            ),
        ),
        gen=GenConfig(out="./out"),
    )

    with pytest.raises(NormError) as exc_info:
        _ensure_postgres_engine(target)

    assert exc_info.value.code == NormErrorCode.INVALID_CONFIG
    assert "postgres" in exc_info.value.message
    assert exc_info.value.context["engine"] == "sqlite"
    assert exc_info.value.context["target"] == "api"
