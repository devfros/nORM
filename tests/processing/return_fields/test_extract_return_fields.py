import pytest

from norm.errors import NormError
from norm.processing import QueryProcessor
from norm.processing.optimize import optimize_query
from norm.schemas.parsing import DBSchema

from ..case_loader import iter_case_queries
from ..fixtures import *  # noqa: F403
from ..golden_cases import discover_processing_case_ids

_CASES = discover_processing_case_ids()
_RETURN_FIELD_CASES = [
    case_id for case_id in _CASES if case_id.startswith("return_fields/")
]


@pytest.mark.parametrize("case_id", _RETURN_FIELD_CASES, indirect=True)
def test_extract_return_fields(
    case_id: str,
    case_dir,
    case_dialect: str,
    case_db_schema: DBSchema,
):
    processor = QueryProcessor(db_schema=case_db_schema)

    for query_name, repo_query, expected in iter_case_queries(case_dir, case_dialect):
        expected_fields = expected.get("properties", [])
        error = expected.get("error", None)

        query = repo_query.sql

        if error:
            with pytest.raises(NormError) as err:
                preprocessed = processor.preprocess(query)
                optimized_query = optimize_query(
                    preprocessed,
                    schema=case_db_schema.map(),
                    dialect=case_db_schema.dialect,
                )
                processor.extract_return_fields(optimized_query)
            assert err.value.code == error.get("code"), query_name
            continue

        preprocessed = processor.preprocess(query)
        optimized_query = optimize_query(
            preprocessed,
            schema=case_db_schema.map(),
            dialect=case_db_schema.dialect,
        )
        return_fields = processor.extract_return_fields(optimized_query)

        assert len(return_fields) == len(expected_fields), query_name

        for field, expected_field in zip(return_fields, expected_fields):
            dict_field = {
                "name": field.name,
                "datatype": field.sql_datatype.sql() if field.sql_datatype else None,
                "table": field.column_ref.table_name if field.column_ref else None,
                "non_column": field.column_ref is None,
            }
            for key, value in expected_field.items():
                assert dict_field.get(key) == value, f"{query_name}.{key} != '{value}'"
