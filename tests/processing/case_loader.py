from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sqlglot import Dialects

from norm.parsing import RepoSqlParser
from norm.schemas.repo import RepoQuery

REPO_NAME = "TestRepo"
DEFAULT_QUERY_NAME = "main"


def dialect_dir(case_dir: Path, dialect: str) -> Path:
    return case_dir / dialect


def resolve_input_path(case_dir: Path, dialect: str) -> Path:
    path = dialect_dir(case_dir, dialect) / "input.sql"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing input.sql for dialect '{dialect}' in '{case_dir}'"
        )
    return path


def load_input_repo(case_dir: Path, dialect: str | Dialects) -> list[RepoQuery]:
    if isinstance(dialect, str):
        dialect = Dialects[dialect.upper()]

    path = resolve_input_path(case_dir, dialect.value)
    repo = RepoSqlParser(dialect).parse_file(path)
    if repo is None or len(repo.queries) == 0:
        raise ValueError(f"No queries parsed from '{path}'")

    return repo.queries


def load_expected_output(case_dir: Path, dialect: str) -> dict[str, Any]:
    path = dialect_dir(case_dir, dialect) / "output.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing output.json for dialect '{dialect}' in '{case_dir}'"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_expected_queries(case_dir: Path, dialect: str) -> dict[str, dict[str, Any]]:
    output = load_expected_output(case_dir, dialect)
    queries = output.get("queries")
    if not isinstance(queries, dict) or len(queries) == 0:
        raise ValueError(
            f"output.json for '{case_dir}/{dialect}' must contain a non-empty 'queries' object"
        )
    return queries


def iter_case_queries(
    case_dir: Path,
    dialect: str | Dialects,
) -> Iterator[tuple[str, RepoQuery, dict[str, Any]]]:
    if isinstance(dialect, str):
        dialect_enum = Dialects[dialect.upper()]
        dialect_key = dialect
    else:
        dialect_enum = dialect
        dialect_key = dialect.value

    repo_queries = {
        query.name: query for query in load_input_repo(case_dir, dialect_enum)
    }
    expected_queries = load_expected_queries(case_dir, dialect_key)

    missing_in_repo = set(expected_queries) - set(repo_queries)
    if missing_in_repo:
        raise ValueError(
            f"output.json references unknown queries {sorted(missing_in_repo)} "
            f"in '{case_dir}/{dialect_key}'"
        )

    for query_name, expected in expected_queries.items():
        yield query_name, repo_queries[query_name], expected
