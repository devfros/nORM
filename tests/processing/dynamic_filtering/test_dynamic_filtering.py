import pytest

from norm.consts import TEMP_PLACEHOLDER_PATTERN
from norm.gen.python.utils.dynamic_filter import build_filter_clauses
from norm.processing import QueryProcessor
from norm.schemas.parsing import DBSchema

from ..case_loader import iter_case_queries
from ..fixtures import *  # noqa: F403
from ..golden_cases import discover_processing_case_ids

_CASES = discover_processing_case_ids()
_DYNAMIC_FILTER_CASES = [
    case_id for case_id in _CASES if case_id.startswith("dynamic_filtering/")
]


@pytest.mark.parametrize("case_id", _DYNAMIC_FILTER_CASES, indirect=True)
def test_dynamic_filtering(
    case_id: str,
    case_dir,
    case_dialect: str,
    case_db_schema: DBSchema,
    dialect,
):
    for query_name, repo_query, expected in iter_case_queries(case_dir, case_dialect):
        versions = expected.get("versions", [])

        processor = QueryProcessor(
            db_schema=case_db_schema,
            enforce_dynamic_filtering=True,
        )

        query = processor.preprocess(repo_query.sql)
        query = processor.dynamic_filter(query.copy(), False)

        filters = {
            TEMP_PLACEHOLDER_PATTERN.format(key): value.dump()
            for key, value in processor._filters.items()
        }

        query_str = query.sql(comments=True)

        assert filters is not None, query_name

        for version in versions:
            params = {item: item for item in version.get("params", [])}
            expected_query = version.get("query")
            built = build_filter_clauses(
                query_str,
                params,
                filters,
            )
            assert built.strip() == expected_query.strip(), query_name
