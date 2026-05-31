from pathlib import Path

from sqlglot import Dialects

from norm.parsing import RepoSqlParser, SchemaSqlParser
from norm.processing.processor import QueryProcessor


def test_sqlite_typeless_columns_query_processes() -> None:
    case = Path("tests/gen/e2e/python/cases/untyped_columns/sqlite")
    db_schema = SchemaSqlParser(Dialects.SQLITE).parse_file(case / "in/schema.sql")
    repo = RepoSqlParser(Dialects.SQLITE).parse_file(case / "in/repos/repo.sql")

    assert db_schema is not None
    assert db_schema.get_table("repro") is not None

    processor = QueryProcessor(db_schema)
    processed = processor.process(repo.queries[0])

    assert processed.returns is not None
    assert set(processed.returns.fields) == {"id", "name", "seq"}
    assert "id" in processed.parameters
