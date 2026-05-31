from __future__ import annotations

import logging
import sys
from importlib.metadata import PackageNotFoundError, version

import click

from norm.cli.completion import complete_config
from norm.cli.context import (
    EXIT_ERROR,
    EXIT_USAGE,
    CliContext,
    ErrorFormat,
    resolve_project,
)
from norm.cli.display import render_error, render_unexpected_error
from norm.cli.lazy import LazyGroup
from norm.errors import NormError

WORKFLOW_EPILOG = """
Workflow:

  norm init
  norm schema pull
  norm generate
  norm check

Commands:

  Setup:      init, targets
  Codegen:    generate, check
  Schema:     schema pull
  Migrations: migrations (not yet implemented)
"""


def _package_version() -> str:
    try:
        return version("nORM")
    except PackageNotFoundError:
        return "0.0.0"


class NormGroup(LazyGroup):
    def invoke(self, ctx: click.Context) -> object:
        try:
            return super().invoke(ctx)
        except NormError as err:
            cli_ctx = ctx.obj
            if isinstance(cli_ctx, CliContext):
                render_error(err, cli_ctx)
            else:
                render_error(
                    err,
                    CliContext(
                        config_path=resolve_project(None, None)[0],
                        base_dir=resolve_project(None, None)[1],
                        verbose=0,
                        quiet=False,
                        no_color=False,
                        error_format=ErrorFormat.HUMAN,
                    ),
                )
            ctx.exit(EXIT_ERROR)


@click.group("norm", cls=NormGroup, epilog=WORKFLOW_EPILOG)
@click.option(
    "--config",
    type=click.Path(path_type=str),
    default=None,
    help="Path to norm.yaml.",
    shell_complete=complete_config,
)
@click.option(
    "--cwd",
    type=click.Path(path_type=str),
    default=None,
    help="Project root directory.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Suppress non-error output.",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output.",
)
@click.option(
    "--error-format",
    type=click.Choice([item.value for item in ErrorFormat], case_sensitive=False),
    default=ErrorFormat.HUMAN.value,
    help="Error output format.",
)
@click.version_option(version=_package_version(), prog_name="norm")
@click.pass_context
def cli(
    ctx: click.Context,
    config: str | None,
    cwd: str | None,
    verbose: int,
    quiet: bool,
    no_color: bool,
    error_format: str,
) -> None:
    """nORM command-line interface."""
    config_path, base_dir = resolve_project(config, cwd)
    ctx.obj = CliContext(
        config_path=config_path,
        base_dir=base_dir,
        verbose=verbose,
        quiet=quiet,
        no_color=no_color,
        error_format=ErrorFormat(error_format.lower()),
    )


cli.register_lazy("init", "norm.cli.init", "init")
cli.register_lazy("generate", "norm.cli.gen", "generate")
cli.register_lazy("check", "norm.cli.gen", "check")
cli.register_lazy("schema", "norm.cli.schema", "schema")
cli.register_lazy("migrations", "norm.cli.migrations", "migrations")
cli.register_lazy("targets", "norm.cli.targets", "targets")


def main() -> None:
    logging.getLogger("sqlglot").setLevel(logging.ERROR)
    try:
        cli.main(standalone_mode=True, prog_name="norm")
    except click.UsageError:
        sys.exit(EXIT_USAGE)
    except click.ClickException:
        raise
    except NormError as err:
        ctx = click.get_current_context(silent=True)
        cli_ctx = ctx.obj if ctx is not None else None
        if cli_ctx is not None:
            render_error(err, cli_ctx)
        else:
            render_error(
                err,
                CliContext(
                    config_path=resolve_project(None, None)[0],
                    base_dir=resolve_project(None, None)[1],
                    verbose=0,
                    quiet=False,
                    no_color=False,
                    error_format=ErrorFormat.HUMAN,
                ),
            )
        sys.exit(EXIT_ERROR)
    except Exception as err:
        ctx = click.get_current_context(silent=True)
        cli_ctx = (
            ctx.obj
            if ctx is not None
            else CliContext(
                config_path=resolve_project(None, None)[0],
                base_dir=resolve_project(None, None)[1],
                verbose=0,
                quiet=False,
                no_color=False,
                error_format=ErrorFormat.HUMAN,
            )
        )
        render_unexpected_error(err, cli_ctx)
        sys.exit(EXIT_ERROR)
