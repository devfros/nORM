from sqlglot import Dialects, parse_one

from norm.parsing.schema_parser import SchemaSqlParser
from norm.processing import QueryProcessor
from norm.processing.optimize import optimize_query
from norm.schemas.parsing import DBSchema


def test_db_schema_map_includes_pg_timezone_names() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    mapping = schema.map()

    assert "pg_catalog" in mapping.mapping
    assert "pg_timezone_names" in mapping.mapping["pg_catalog"]
    columns = mapping.mapping["pg_catalog"]["pg_timezone_names"]
    assert set(columns) >= {"name", "abbrev", "utc_offset", "is_dst"}


def test_get_field_resolves_catalog_view_columns() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    field = schema.get_field("name", "pg_timezone_names", "pg_catalog")

    assert field is not None
    assert field.name == "name"
    assert field.sql_datatype is not None
    assert field.sql_datatype.sql() == "TEXT"
    assert field.column_ref is not None
    assert field.column_ref.table_name == "pg_timezone_names"


def test_get_field_resolves_postgres_system_columns_on_user_tables() -> None:
    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(
        "CREATE TABLE test (id INT);"
    )
    assert schema is not None

    field = schema.get_field("tableoid", "test")
    assert field is not None
    assert field.sql_datatype is not None
    assert field.sql_datatype.sql() == "OID"
    assert field.column_ref is not None
    assert field.column_ref.table_name == "test"


def test_pg_timezone_names_select_star_expands() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    processor = QueryProcessor(db_schema=schema)
    query = parse_one(
        "SELECT * FROM pg_catalog.pg_timezone_names",
        dialect="postgres",
    )
    preprocessed = processor.preprocess(query)
    optimized = optimize_query(
        preprocessed,
        schema=schema.map(),
        dialect=schema.dialect,
    )

    assert len(optimized.expressions) == 4

    fields = processor.extract_return_fields(optimized)
    assert [field.name for field in fields] == [
        "name",
        "abbrev",
        "utc_offset",
        "is_dst",
    ]
    assert all(field.column_ref and field.column_ref.table_name == "pg_timezone_names" for field in fields)


def test_select_system_columns() -> None:
    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(
        "CREATE TABLE test (id INT);"
    )
    assert schema is not None

    processor = QueryProcessor(db_schema=schema)
    query = parse_one(
        "SELECT tableoid, xmin, cmin, xmax, cmax, ctid FROM test",
        dialect="postgres",
    )
    preprocessed = processor.preprocess(query)
    optimized = optimize_query(
        preprocessed,
        schema=schema.map(),
        dialect=schema.dialect,
    )
    fields = processor.extract_return_fields(optimized)

    assert [field.name for field in fields] == [
        "tableoid",
        "xmin",
        "cmin",
        "xmax",
        "cmax",
        "ctid",
    ]
    assert [field.sql_datatype.sql() for field in fields] == [
        "OID",
        "xid",
        "cid",
        "xid",
        "cid",
        "tid",
    ]
