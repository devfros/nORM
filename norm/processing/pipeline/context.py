from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlglot import Dialects

    from norm.schemas.dynamic_filter import DynamicFilter
    from norm.schemas.parsing import DBSchema
    from norm.schemas.repo import DynamicOrderby


@dataclass
class ProcessingContext:
    db_schema: DBSchema
    param_template: str
    enforce_dynamic_filtering: bool = False
    lists: dict[str, str] = field(default_factory=dict)
    patches: dict[str, str] = field(default_factory=dict)
    ords: dict[str, DynamicOrderby] = field(default_factory=dict)
    filters: dict[str, DynamicFilter] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.dialect: Dialects = self.db_schema.dialect

    def reset_state(self) -> None:
        self.lists.clear()
        self.patches.clear()
        self.ords.clear()
        self.filters.clear()
