from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .core import CoreSchema


@dataclass
class DynamicFilter(CoreSchema):
    clause: Literal["WHERE", "HAVING"]
    tree: FilterTree

    def dump(self) -> dict:
        return self.model_dump(exclude_none=True)


@dataclass
class FilterTree(CoreSchema):
    t: str | None = None  # Connector type: OR, AND, NOT
    g: bool | None = None  # Whether the node is parenthesized
    p: list[str] | None = None  # Required parameters to include the node
    l: FilterTree | None = None  # Left node  # noqa: E741
    r: FilterTree | None = None  # Right node
    v: str | None = None  # Value (sql string containing a condition)
