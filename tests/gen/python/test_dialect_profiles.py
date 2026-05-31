from pathlib import Path

import pytest
from sqlglot import Dialects, exp
from sqlglot.expressions import DType

from norm.consts import MetaKeys, SUPPORTED_SQL_DIALECTS
from norm.gen.python.dialects import DIALECT_DRIVER_MAP, get_python_dialect_profile
from norm.gen.python.generator import PythonGenerator
from norm.gen.python.types_map import get_python_type
from norm.schemas.config import GenConfig, PythonGenConfig
from norm.schemas.parsing import (
    DBSchema,
    FieldDefinition,
    ModelDefinition,
    ModelKind,
    ParameterDefinition,
    ParameterKind,
)
from norm.schemas.repo import ProcessedQuery, QueryCommandEnum, Repo


def _datatype(kind: DType) -> exp.DataType:
    return exp.DataType.build(kind)


def _authors_model() -> ModelDefinition:
    return ModelDefinition(
        name="authors",
        fields={
            "id": FieldDefinition(name="id", datatype=_datatype(DType.INT)),
            "name": FieldDefinition(name="name", datatype=_datatype(DType.TEXT)),
        },
        kind=ModelKind.TABLE,
    )


def _processed_no_params_query() -> ProcessedQuery:
    return ProcessedQuery(
        name="get_all_authors",
        command=QueryCommandEnum.MANY,
        comment=None,
        query_str="SELECT id, name\nFROM authors",
        parameters={},
        ordered_params_seq=[],
        returns=_authors_model(),
        lists={},
        patches={},
        ords={},
    )


def _processed_list_query() -> ProcessedQuery:
    ids = ParameterDefinition(
        name="ids",
        datatype=_datatype(DType.ARRAY),
        kind=ParameterKind.LIST
    )

    return ProcessedQuery(
        name="list_authors",
        command=QueryCommandEnum.MANY,
        comment=None,
        query_str=(
            "SELECT id, name\n"
            "FROM authors\n"
            "WHERE id IN (/*LIST1*/)"
        ),
        parameters={"ids": ids},
        ordered_params_seq=["ids"],
        returns=_authors_model(),
        lists={"ids": "/*LIST1*/"},
        patches={},
        ords={},
    )


def _generate_repo_content(
    dialect: Dialects,
    asynchronous: bool = True,
    *,
    processed_queries: list[ProcessedQuery] | None = None,
) -> str:
    author = _authors_model()
    db_schema = DBSchema(dialect=dialect, tables={"authors": author})
    repo = Repo(
        name="AuthorsRepo",
        file_path=Path("authors_repo.sql"),
        queries=[],
        processed_queries=processed_queries or [_processed_list_query()],
    )
    config = GenConfig(
        out=".",
        python=PythonGenConfig(
            asynchronous=asynchronous,
            models="dataclasses",
            max_params=1,
        ),
    )

    output = PythonGenerator(config, dialect).generate(db_schema, [repo])
    return dict(output.iter_files())[Path("authors_repo.py")]


@pytest.mark.parametrize("dialect", list(Dialects))
def test_no_params_query_omits_params_and_passes_query_only(dialect: Dialects):
    repo_content = _generate_repo_content(
        dialect,
        processed_queries=[_processed_no_params_query()],
    )

    assert "params =" not in repo_content
    assert "execute(query)" in repo_content
    assert "execute(query, params)" not in repo_content


def test_clickhouse_sync_generated_python_closes_cursor():
    repo_content = _generate_repo_content(Dialects.CLICKHOUSE, asynchronous=False)

    assert "from contextlib import closing" in repo_content
    assert "with closing(self.db.cursor()) as cur:" in repo_content


def test_duckdb_sync_generated_python_closes_cursor():
    repo_content = _generate_repo_content(Dialects.DUCKDB, asynchronous=False)

    assert "from contextlib import closing" in repo_content
    assert "with closing(self.db.cursor()) as cur:" in repo_content


@pytest.mark.parametrize(
    "dialect",
    [
        Dialects.POSTGRES,
        Dialects.MYSQL,
        Dialects.SQLITE,
        Dialects.CLICKHOUSE,
        Dialects.DUCKDB,
    ],
)
def test_sync_many_queries_fetch_all_rows(dialect: Dialects):
    repo_content = _generate_repo_content(dialect, asynchronous=False)

    assert "for item in cur.fetchall()" in repo_content
    assert "async for item in cur" not in repo_content


def test_async_many_queries_iterate_cursor():
    repo_content = _generate_repo_content(Dialects.DUCKDB, asynchronous=True)

    assert "async for item in cur" in repo_content
    assert "for item in cur.fetchall()" not in repo_content


def test_every_supported_sql_dialect_has_python_profile():
    profiled_dialects = {dialect.value for dialect in DIALECT_DRIVER_MAP}

    assert profiled_dialects >= SUPPORTED_SQL_DIALECTS
    assert Dialects.CLICKHOUSE.value in profiled_dialects
    assert Dialects.DUCKDB.value in profiled_dialects

    for dialect in DIALECT_DRIVER_MAP:
        for is_async in (True, False):
            profile = get_python_dialect_profile(dialect, is_async)
            assert profile.dialect == dialect
            assert profile.param_template
            assert profile.driver.imports.imports
            assert get_python_type(_datatype(DType.INT), dialect).compiled == "int"
