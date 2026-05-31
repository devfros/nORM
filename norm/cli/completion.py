from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from norm.cli.context import resolve_project
from norm.config import load_norm_config
from norm.consts import CONFIG_FILE

if TYPE_CHECKING:
    import click


def _load_target_names(config: str | None, cwd: str | None) -> list[str]:
    try:
        config_path, _base_dir = resolve_project(config, cwd)
        if not config_path.is_file():
            return []
        norm_config = load_norm_config(config_path)
    except Exception:
        return []
    return sorted(norm_config.targets.keys())


def complete_targets(
    ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    config = ctx.params.get("config")
    cwd = ctx.params.get("cwd")
    if config is None and ctx.parent is not None:
        config = ctx.parent.params.get("config")
    if cwd is None and ctx.parent is not None:
        cwd = ctx.parent.params.get("cwd")
    names = _load_target_names(config, cwd)
    return [name for name in names if name.startswith(incomplete)]


def complete_config(
    ctx: click.Context,
    _param: click.Parameter,
    incomplete: str,
) -> list[str]:
    cwd = ctx.params.get("cwd")
    root = Path(cwd).resolve() if cwd else Path.cwd()
    matches: list[str] = []
    for path in root.rglob(CONFIG_FILE):
        if path.is_file():
            text = str(path)
            if text.startswith(incomplete):
                matches.append(text)
    return matches
