from __future__ import annotations

import importlib
from typing import Any

import click


def load_command(module: str, attr: str) -> click.Command | click.Group:
    loaded = importlib.import_module(module)
    command = getattr(loaded, attr)
    if not isinstance(command, (click.Command, click.Group)):
        msg = f"{module}:{attr} is not a Click command"
        raise TypeError(msg)
    return command


class LazyGroup(click.Group):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._lazy_commands: dict[str, tuple[str, str]] = {}

    def register_lazy(self, name: str, module: str, attr: str) -> None:
        self._lazy_commands[name] = (module, attr)

    def list_commands(self, _ctx: click.Context) -> list[str]:
        return sorted({*self.commands.keys(), *self._lazy_commands.keys()})

    def get_command(
        self,
        ctx: click.Context,
        cmd_name: str,
    ) -> click.Command | None:
        spec = self._lazy_commands.get(cmd_name)
        if spec is None:
            return super().get_command(ctx, cmd_name)

        module, attr = spec
        command = load_command(module, attr)
        self.add_command(command, name=cmd_name)
        del self._lazy_commands[cmd_name]
        return command
