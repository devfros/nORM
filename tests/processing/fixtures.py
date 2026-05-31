from __future__ import annotations

from pathlib import Path

import pytest
from sqlglot import Dialects

from norm.parsing import SchemaSqlParser
from norm.schemas.parsing import DBSchema

from .case_loader import dialect_dir
from .golden_cases import case_dir_for_id


@pytest.fixture
def case_id(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def case_suite(case_id: str) -> str:
    return case_id.split("/")[0]


@pytest.fixture
def case_name(case_id: str) -> str:
    return case_id.split("/")[1]


@pytest.fixture
def case_dialect(case_id: str) -> str:
    return case_id.split("/")[2]


@pytest.fixture
def case_dir(case_id: str) -> Path:
    return case_dir_for_id(case_id)


@pytest.fixture
def dialect(case_dialect: str) -> Dialects:
    return Dialects[case_dialect.upper()]


@pytest.fixture
def case_schema_path(case_dir: Path, case_dialect: str) -> Path:
    schema_path = dialect_dir(case_dir, case_dialect) / "schema.sql"
    if not schema_path.is_file():
        raise FileNotFoundError(
            f"Missing schema.sql for dialect '{case_dialect}' in '{case_dir}'"
        )

    return schema_path


@pytest.fixture
def case_db_schema(case_schema_path: Path, dialect: Dialects) -> DBSchema:
    db_schema = SchemaSqlParser(dialect).parse_file(case_schema_path)
    return db_schema or DBSchema(dialect=dialect)
