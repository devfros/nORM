from sqlglot import Dialects, parse_one

from norm.processing.extracting import get_projection_expressions
from norm.processing.optimize.qualify_columns import qualify_columns
from norm.processing.optimize.relation_nodes import tables_for_returning_shadow
from norm.processing.processor import QueryProcessor
from norm.parsing import SchemaSqlParser


def _postgres_schema():
    return SchemaSqlParser(Dialects.POSTGRES).parse_sql(
        """
        CREATE SCHEMA td3;
        CREATE TABLE td3.codes (id serial primary key, hash text);
        CREATE TABLE td3.test_codes (
            id serial primary key,
            test_id integer not null,
            code_hash text not null
        );
        CREATE TABLE authors (id serial primary key, name text, rating integer);
        """
    )


def test_tables_for_returning_shadow_unqualified_star_ignores_from_cte() -> None:
    query = parse_one(
        """
        WITH cc AS (
          UPDATE td3.codes SET hash = 'x' RETURNING hash
        )
        UPDATE td3.test_codes
        SET code_hash = cc.hash
        FROM cc
        RETURNING *;
        """,
        dialect="postgres",
    )
    projections = get_projection_expressions(query)

    tables = tables_for_returning_shadow(query, projections)

    assert len(tables) == 1
    assert tables[0].name == "test_codes"
    assert tables[0].db == "td3"


def test_tables_for_returning_shadow_qualified_star_includes_alias() -> None:
    query = parse_one(
        "UPDATE authors a SET rating = 1 WHERE a.id = 1 RETURNING a.*;",
        dialect="postgres",
    )
    projections = get_projection_expressions(query)

    tables = tables_for_returning_shadow(query, projections)

    assert len(tables) == 1
    assert tables[0].name == "authors"
    assert tables[0].alias == "a"


def test_qualify_columns_expands_returning_star_with_from_cte() -> None:
    schema = _postgres_schema()
    query = parse_one(
        """
        WITH cc AS (
          UPDATE td3.codes SET hash = 'h' RETURNING hash
        )
        UPDATE td3.test_codes
        SET code_hash = cc.hash
        FROM cc
        RETURNING *;
        """,
        dialect="postgres",
    )

    qualified = qualify_columns(query, schema=schema.map(), dialect=Dialects.POSTGRES)
    projections = get_projection_expressions(qualified)

    assert projections
    assert all(not projection.is_star for projection in projections)


def test_processor_handles_update_cte_returning_star() -> None:
    schema = _postgres_schema()
    query = parse_one(
        """
        WITH cc AS (
          UPDATE td3.codes SET hash = 'h' RETURNING hash
        )
        UPDATE td3.test_codes
        SET code_hash = cc.hash
        FROM cc
        RETURNING *;
        """,
        dialect="postgres",
    )
    from norm.schemas.repo import QueryCommandEnum, RepoQuery

    processor = QueryProcessor(schema)
    processed = processor.process(
        RepoQuery(name="UpdateCode", command=QueryCommandEnum.ONE, sql=query, comment=None)
    )

    assert processed.returns is not None
    assert len(processed.returns.fields) == 3
