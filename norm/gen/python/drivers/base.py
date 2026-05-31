from dataclasses import dataclass

from norm.gen.dialect_profile import DialectProfile
from norm.gen.python.schemas import ImportData
from norm.schemas.repo import QueryCommandEnum


@dataclass(frozen=True)
class DriverProfile:
    imports: ImportData
    param_template: str
    unsupported_query_commands: set[QueryCommandEnum] | None = None
    close_sync_cursor: bool = False
    named_params: bool = False


@dataclass(frozen=True)
class PythonDialectProfile(DialectProfile):
    driver: DriverProfile
