import pytest

from norm.errors import NormError
from norm.processing import QueryProcessor
from norm.processing.optimize import optimize_query
from norm.schemas.parsing import DBSchema

from ..case_loader import iter_case_queries
from ..fixtures import *  # noqa: F403
from ..golden_cases import discover_processing_case_ids

_CASES = discover_processing_case_ids()
_PARAMETER_CASES = [case_id for case_id in _CASES if case_id.startswith("parameters/")]


@pytest.mark.parametrize("case_id", _PARAMETER_CASES, indirect=True)
def test_extract_placeholders(
    case_id: str,
    case_dir,
    case_dialect: str,
    case_db_schema: DBSchema,
    dialect,
):
    processor = QueryProcessor(db_schema=case_db_schema)

    for query_name, repo_query, expected in iter_case_queries(case_dir, case_dialect):
        output_parameters = expected.get("parameters", None)
        error = expected.get("error", None)

        query = repo_query.sql

        if error:
            with pytest.raises(NormError) as err:
                preprocessed = processor.preprocess(query)
                optimized_query = optimize_query(
                    preprocessed,
                    schema=case_db_schema.map(),
                    dialect=case_db_schema.dialect,
                    db_schema=case_db_schema,
                )
                processor.extract_parameters(optimized_query)

            assert err.value.code == error.get("code"), query_name
            continue

        preprocessed = processor.preprocess(query)
        optimized_query = optimize_query(
            preprocessed,
            schema=case_db_schema.map(),
            dialect=case_db_schema.dialect,
            db_schema=case_db_schema,
        )
        parameters = processor.extract_parameters(optimized_query)

        assert output_parameters is not None, query_name

        assert len(parameters) == len(output_parameters), query_name

        for name, param in parameters.items():
            assert name in output_parameters, f"'{query_name}.{name}' is missing"

            expected_param = output_parameters.get(name)

            dict_param = {
                "name": name,
                "datatype": param.sql_datatype.sql() if param.sql_datatype else None,
                "nullable": param.constraints.nullable,
                "optional": param.constraints.optional,
            }
            for key, value in expected_param.items():
                assert dict_param.get(key) == value, f"{query_name}.{key} != '{value}'"
