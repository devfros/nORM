from __future__ import annotations

import sys

import click

from norm.cli.context import EXIT_USAGE, CliContext
from norm.cli.display import print_warning
from norm.cli.options import pass_cli_context

NOT_IMPLEMENTED_MESSAGE = "Migrations are not implemented yet."


@click.group("migrations")
@click.pass_obj
def migrations(_cli_ctx: CliContext) -> None:
    """Database migration commands."""


@migrations.command("check")
@pass_cli_context
def migrations_check(cli_ctx: CliContext) -> None:
    """Check migration status."""
    print_warning(cli_ctx, NOT_IMPLEMENTED_MESSAGE)
    sys.exit(EXIT_USAGE)


@migrations.command("revision")
@pass_cli_context
def migrations_revision(cli_ctx: CliContext) -> None:
    """Create a new migration revision."""
    print_warning(cli_ctx, NOT_IMPLEMENTED_MESSAGE)
    sys.exit(EXIT_USAGE)
