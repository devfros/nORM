from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from norm.config import load_norm_config
from norm.consts import CONFIG_FILE

if TYPE_CHECKING:
    from norm.schemas import NormConfig

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


class ErrorFormat(StrEnum):
    HUMAN = "human"
    JSON = "json"
    GITHUB = "github"


@dataclass(frozen=True)
class CliContext:
    config_path: Path
    base_dir: Path
    verbose: int
    quiet: bool
    no_color: bool
    error_format: ErrorFormat


def resolve_project(
    config: str | None,
    cwd: str | None,
) -> tuple[Path, Path]:
    root = Path(cwd).resolve() if cwd else Path.cwd()
    config_path = Path(config).resolve() if config else (root / CONFIG_FILE).resolve()
    base_dir = root if cwd else config_path.parent
    return config_path, base_dir


def load_config(ctx: CliContext) -> NormConfig:
    return load_norm_config(ctx.config_path)


def target_path(base_dir: Path, relative: str) -> Path:
    return (base_dir / relative).resolve()
