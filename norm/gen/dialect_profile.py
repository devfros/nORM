from dataclasses import dataclass

from sqlglot import Dialects

from norm.schemas.repo import QueryCommandEnum


@dataclass(frozen=True)
class DialectProfile:
    dialect: Dialects
    param_template: str
    unsupported_query_commands: set[QueryCommandEnum]
