from __future__ import annotations

import re
import subprocess
import time
from typing import TYPE_CHECKING

import click
from sqlglot import Dialects, parse
from sqlglot.errors import ParseError

from norm.cli.context import CliContext, load_config, target_path
from norm.cli.display import print_info, print_schema_pull_success
from norm.cli.options import pass_cli_context, target_option
from norm.errors import NormError, NormErrorCode
from norm.schemas.config import SqlConfig, TargetConfig

if TYPE_CHECKING:
    from pathlib import Path

    from norm.schemas.config import SqlConfig, TargetConfig

POSTGRES_ENGINE = Dialects.POSTGRES.value

META_COMMAND_PATTERN = re.compile(r"^\\[A-Za-z!?;][^\n]*$")
SET_COMMAND_PATTERN = re.compile(r"^SET\s+", re.IGNORECASE)
PG_CATALOG_CONFIG_PATTERN = re.compile(
    r"^SELECT\s+pg_catalog\.set_config\s*\(",
    re.IGNORECASE,
)

SCHEMA_EPILOG = """
Examples:

  norm schema pull
  norm schema pull --target default
"""


def _trim_error_text(text: str) -> str:
    return " ".join(text.split())[:400]


def clean_schema_text(schema: str) -> str:
    lines = schema.splitlines()
    cleaned_lines = [
        line
        for line in lines
        if not META_COMMAND_PATTERN.match(line)
        and not SET_COMMAND_PATTERN.match(line)
        and not PG_CATALOG_CONFIG_PATTERN.match(line)
    ]
    cleaned_schema = "\n".join(cleaned_lines)
    if schema.endswith("\n") and cleaned_schema:
        return f"{cleaned_schema}\n"
    return cleaned_schema


def _ensure_postgres_engine(target: TargetConfig) -> None:
    engine = target.sql.engine.strip().lower()
    if engine != POSTGRES_ENGINE:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Schema pull is only supported for engine 'postgres'.",
            hint=(
                "Set sql.engine to postgres for this target, "
                "or skip pull for other engines."
            ),
            context={"engine": target.sql.engine, "target": target.name},
        )


def pull_db_schema(sql_config: SqlConfig) -> str:
    connection = sql_config.migrations.connection if sql_config.migrations else None
    if not connection:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Schema pull requires 'sql.migrations.connection'.",
            hint="Add a postgres connection URL to 'sql.migrations.connection'.",
            context={"db_schema": sql_config.db_schema},
        )

    pg_dump_command = [
        "pg_dump",
        "--schema-only",
        "--no-owner",
        "--no-privileges",
        "--dbname",
        connection,
    ]

    try:
        output = subprocess.run(
            pg_dump_command,
            check=True,
            text=True,
            capture_output=True,
        ).stdout
        if output.strip():
            return output
    except FileNotFoundError as err:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Schema pull requires postgres client tools.",
            hint="Install 'pg_dump' and retry the command.",
            context={"connection": connection},
        ) from err
    except subprocess.CalledProcessError as err:
        error_text = _trim_error_text(err.stderr)
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Failed to pull schema with pg_dump.",
            hint="Check connection URL and database access permissions.",
            context={"connection": connection, "details": error_text},
        ) from err

    raise NormError(
        code=NormErrorCode.INVALID_CONFIG,
        message="Database has no visible schema to pull.",
        hint="Ensure the target database contains schema objects to pull.",
        context={"connection": connection},
    )


def format_pulled_schema(raw_schema: str, dialect: Dialects) -> str:
    cleaned = clean_schema_text(raw_schema)
    if not cleaned.strip():
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Database has no visible schema to pull.",
            hint="Ensure the target database contains schema objects to pull.",
        )

    try:
        statements = parse(cleaned, dialect=dialect)
    except ParseError as err:
        raise NormError(
            code=NormErrorCode.SQL_PARSE_FAILED,
            message="Failed to parse pulled schema SQL.",
            hint="Report this pg_dump output if the database schema should be valid.",
            context={"details": _trim_error_text(str(err))},
        ) from err

    if not statements:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Database has no visible schema to pull.",
            hint="Ensure the target database contains schema objects to pull.",
        )

    schema_file_content = ""
    for statement in statements:
        content = statement.sql(
            pretty=True,
            comments=False,
            max_text_width=50,
            dialect=dialect,
        )
        schema_file_content += content
        schema_file_content += ";"
        schema_file_content += "\n\n"

    return schema_file_content


def pull_target_db_schema(
    target: TargetConfig,
    *,
    base_dir: Path,
    cli_ctx: CliContext,
) -> tuple[Path, int, int]:
    _ensure_postgres_engine(target)
    print_info(
        cli_ctx,
        f"Pulling schema for target '{target.name}'...",
        style="bold yellow",
    )
    started = time.perf_counter()
    dialect = Dialects.POSTGRES

    raw_schema = pull_db_schema(target.sql)
    schema_file_content = format_pulled_schema(raw_schema, dialect)

    schema_path = target_path(base_dir, target.sql.db_schema)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    if not schema_path.exists():
        schema_path.touch()
    schema_path.write_text(schema_file_content, encoding="utf-8")

    line_count = len(schema_file_content.splitlines())
    duration_ms = int((time.perf_counter() - started) * 1000)
    return schema_path, line_count, duration_ms


@click.group("schema")
@click.pass_obj
def schema(_cli_ctx: CliContext) -> None:
    """Schema management commands."""


@schema.command("pull")
@target_option
@pass_cli_context
def pull(cli_ctx: CliContext, target: str | None) -> None:
    """Pull schema definitions from database into schema files."""
    config = load_config(cli_ctx)

    if target:
        target_config = config.targets.get(target)
        if target_config is None:
            raise NormError(
                code=NormErrorCode.UNKNOWN_TARGET,
                message=f"Target '{target}' is not in config file.",
            )
        targets = [target_config]
    else:
        targets = list(config.targets.values())

    for target_config in targets:
        schema_path, line_count, duration_ms = pull_target_db_schema(
            target_config,
            base_dir=cli_ctx.base_dir,
            cli_ctx=cli_ctx,
        )
        print_schema_pull_success(
            cli_ctx,
            target_config.name,
            schema_path,
            line_count,
            duration_ms,
        )


pull.epilog = SCHEMA_EPILOG
