from __future__ import annotations

from typing import TYPE_CHECKING

import click
from rich.table import Table

from norm.cli.context import CliContext, load_config, target_path
from norm.cli.display import get_console
from norm.cli.options import pass_cli_context, target_option
from norm.errors import NormError, NormErrorCode

if TYPE_CHECKING:
    from pathlib import Path


def _relative(base_dir: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)


@click.command("targets")
@target_option
@pass_cli_context
def targets(cli_ctx: CliContext, target: str | None) -> None:
    """List configured targets and their paths."""
    config = load_config(cli_ctx)

    if target and target not in config.targets:
        raise NormError(
            code=NormErrorCode.UNKNOWN_TARGET,
            message=f"Target '{target}' is not in config file.",
        )

    selected = [config.targets[target]] if target else list(config.targets.values())

    table = Table(title="nORM targets", show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Engine")
    table.add_column("Schema")
    table.add_column("Repositories")
    table.add_column("Output")

    for item in selected:
        schema = target_path(cli_ctx.base_dir, item.sql.db_schema)
        repos = target_path(cli_ctx.base_dir, item.sql.repositories)
        out = target_path(cli_ctx.base_dir, item.gen.out)
        table.add_row(
            item.name,
            item.sql.engine,
            _relative(cli_ctx.base_dir, schema),
            _relative(cli_ctx.base_dir, repos),
            _relative(cli_ctx.base_dir, out),
        )

    get_console(cli_ctx).print(table)
