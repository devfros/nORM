from __future__ import annotations

from importlib import resources
from typing import TYPE_CHECKING

import click
import yaml

from norm.cli.context import CliContext, load_config, target_path
from norm.cli.display import print_path_tree, print_success
from norm.cli.options import pass_cli_context
from norm.consts import DEFAULT_CONFIG
from norm.schemas import NormConfig

if TYPE_CHECKING:
    from pathlib import Path


INIT_EPILOG = """
Examples:

  norm init
  norm init --dry-run
  norm init --force
"""


def _default_config() -> NormConfig:
    default_yaml = (
        resources.files("norm.config")
        .joinpath(DEFAULT_CONFIG)
        .read_text(encoding="utf-8")
    )
    return NormConfig.from_dict(yaml.safe_load(default_yaml) or {})


def _append_missing_target_paths(
    paths: list[Path],
    cli_ctx: CliContext,
    config: NormConfig,
) -> None:
    for target in config.targets.values():
        repos = target_path(cli_ctx.base_dir, target.sql.repositories)
        if not repos.exists():
            paths.append(repos)
        schema = target_path(cli_ctx.base_dir, target.sql.db_schema)
        if not schema.parent.exists():
            paths.append(schema.parent)
        if not schema.exists():
            paths.append(schema)


def _planned_paths(cli_ctx: CliContext) -> list[Path]:
    paths: list[Path] = []
    if not cli_ctx.config_path.is_file():
        paths.append(cli_ctx.config_path)
        _append_missing_target_paths(paths, cli_ctx, _default_config())
        return paths
    config = load_config(cli_ctx)
    _append_missing_target_paths(paths, cli_ctx, config)
    return paths


def _all_paths_exist(cli_ctx: CliContext) -> bool:
    if not cli_ctx.config_path.is_file():
        return False
    config = load_config(cli_ctx)
    for target in config.targets.values():
        repos = target_path(cli_ctx.base_dir, target.sql.repositories)
        schema = target_path(cli_ctx.base_dir, target.sql.db_schema)
        if not repos.is_dir() or not schema.is_file():
            return False
    return True


@click.command("init")
@click.option("--dry-run", is_flag=True, help="Show what would be created.")
@click.option(
    "--force",
    is_flag=True,
    help="Create missing paths without overwriting norm.yaml.",
)
@pass_cli_context
def init(cli_ctx: CliContext, dry_run: bool, force: bool) -> None:
    """Initialize project config and required target directories."""
    if cli_ctx.config_path.is_file() and _all_paths_exist(cli_ctx) and not force:
        print_success(cli_ctx, "Already initialized")
        return

    if dry_run:
        print_path_tree(cli_ctx, "Would create", _planned_paths(cli_ctx))
        return

    created: list[Path] = []

    if not cli_ctx.config_path.is_file():
        cli_ctx.config_path.parent.mkdir(parents=True, exist_ok=True)
        default_yaml = (
            resources.files("norm.config")
            .joinpath(DEFAULT_CONFIG)
            .read_text(encoding="utf-8")
        )
        cli_ctx.config_path.write_text(default_yaml, encoding="utf-8")
        created.append(cli_ctx.config_path)

    config = load_config(cli_ctx)

    for target in config.targets.values():
        repos = target_path(cli_ctx.base_dir, target.sql.repositories)
        if not repos.exists():
            repos.mkdir(parents=True, exist_ok=True)
            created.append(repos)
        schema = target_path(cli_ctx.base_dir, target.sql.db_schema)
        if not schema.parent.exists():
            schema.parent.mkdir(parents=True, exist_ok=True)
            created.append(schema.parent)
        if not schema.exists():
            schema.touch()
            created.append(schema)

    if created:
        print_path_tree(cli_ctx, "Initialized", created)
    print_success(cli_ctx, "Initialized")


init.epilog = INIT_EPILOG
