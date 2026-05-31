from __future__ import annotations

import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import click

from norm.cli.completion import complete_targets

if TYPE_CHECKING:
    from collections.abc import Callable


def target_option[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    option = click.option(
        "--target",
        "-t",
        default=None,
        type=str,
        help="Target environment",
        shell_complete=complete_targets,
    )
    return option(command)


def pass_cli_context[**P, R](command: Callable[P, R]) -> Callable[P, R]:
    @click.pass_obj
    @functools.wraps(command)
    def wrapper(cli_ctx: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        return command(cli_ctx, *args, **kwargs)

    return wrapper
