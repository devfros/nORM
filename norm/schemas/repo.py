from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from norm.utils.switch_case import camel_to_snake, snake_to_pascal

from .core import CoreSchema

if TYPE_CHECKING:
    from pathlib import Path

    from sqlglot import exp

    from norm.schemas.dynamic_filter import DynamicFilter
    from norm.schemas.parsing import (
        FieldDefinition,
        ModelDefinition,
        ParameterDefinition,
    )


class QueryCommandEnum(StrEnum):
    ONE = "one"
    MANY = "many"
    EXEC = "exec"
    EXECROWS = "execrows"
    EXECLASTID = "execlastid"


@dataclass
class DynamicOrderby(CoreSchema):
    table_name: str
    columns: list[str]
    order_by: str = "order_by"
    desc: str = "desc"


@dataclass
class RepoQuery(CoreSchema):
    name: str
    sql: exp.Expr
    comment: str | None
    command: QueryCommandEnum = QueryCommandEnum.ONE
    line: int | None = None


@dataclass
class ProcessedQuery(CoreSchema):
    name: str
    command: QueryCommandEnum
    comment: str | None

    query_str: str

    parameters: dict[str, ParameterDefinition]
    ordered_params_seq: list[str]

    returns: FieldDefinition | ModelDefinition | None

    lists: dict[str, str]
    patches: dict[str, str]
    ords: dict[str, DynamicOrderby]
    filters: dict[str, DynamicFilter] | None = None


@dataclass
class Repo(CoreSchema):
    name: str
    file_path: Path
    queries: list[RepoQuery]
    processed_queries: list[ProcessedQuery]

    @property
    def model_name(self):
        return snake_to_pascal(self.name)

    @property
    def file_name(self):
        return camel_to_snake(self.file_path.stem)
