import pytest
from sqlglot import Dialects, exp

from norm.consts import MetaKeys
from norm.errors import NormError, NormErrorCode
from norm.parsing import SchemaSqlParser
from norm.schemas.identifiers import identifier_aliases
from norm.schemas.parsing import (
    CatalogSource,
    ColumnRef,
    DBSchema,
    EnumDefinition,
    FieldDefinition,
    FunctionKind,
    LiteralValue,
    function_signature_key,
    ModelDefinition,
    ModelKind,
)


def test_db_schema_uses_dialect_default_catalogs() -> None:
    assert DBSchema(dialect=Dialects.POSTGRES).default_catalog == "public"
    assert DBSchema(dialect=Dialects.SQLITE).default_catalog == "main"
    assert DBSchema(dialect=Dialects.DUCKDB).default_catalog == "main"
    assert DBSchema(dialect=Dialects.MYSQL).default_catalog == "default"
    assert DBSchema(dialect=Dialects.CLICKHOUSE).default_catalog == "default"


def test_db_schema_map_is_catalog_scoped() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    schema.declare_catalog("app")
    schema.add_table(
        ModelDefinition(
            name="users",
            catalog_name="app",
            fields={"id": FieldDefinition("id", exp.DataType.build("int"))},
            kind=ModelKind.TABLE,
        )
    )

    schema_map = schema.map().mapping

    assert set(schema_map) == {"app", "pg_catalog"}
    assert list(schema_map["app"]) == ["users"]
    assert "pg_timezone_names" in schema_map["pg_catalog"]
    assert "id" in schema_map["app"]["users"]
    assert schema_map["app"]["users"]["id"].meta[MetaKeys.CATALOG_NAME] == "app"
    assert schema_map["app"]["users"]["id"].meta[MetaKeys.TABLE_NAME] == "users"


def test_identifier_aliases_preserve_quoted_postgres_names() -> None:
    assert identifier_aliases("Users", Dialects.POSTGRES, quoted=True) == ("Users",)


def test_identifier_aliases_fold_quoted_sqlite_names() -> None:
    assert identifier_aliases("Users", Dialects.SQLITE, quoted=True) == (
        "Users",
        "users",
    )


def test_db_schema_map_respects_quoted_identifier_aliases() -> None:
    postgres_schema = DBSchema(dialect=Dialects.POSTGRES)
    postgres_schema.add_table(
        ModelDefinition(
            name="Users",
            fields={
                "ID": FieldDefinition(
                    "ID",
                    exp.DataType.build("int"),
                    quoted=True,
                )
            },
            kind=ModelKind.TABLE,
            quoted=True,
        )
    )

    sqlite_schema = DBSchema(dialect=Dialects.SQLITE)
    sqlite_schema.add_table(
        ModelDefinition(
            name="Users",
            fields={
                "ID": FieldDefinition(
                    "ID",
                    exp.DataType.build("int"),
                    quoted=True,
                )
            },
            kind=ModelKind.TABLE,
            quoted=True,
        )
    )

    assert "users" not in postgres_schema.map().mapping["public"]
    assert "users" in sqlite_schema.map().mapping["main"]
    assert "id" in sqlite_schema.map().mapping["main"]["users"]


def test_schema_lookups_support_catalog_qualified_names() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    schema.declare_catalog("app")
    table = ModelDefinition(
        name="users",
        catalog_name="app",
        kind=ModelKind.TABLE,
    )
    schema.add_table(table)

    assert schema.get_table("users", "app") is table
    assert schema.get_table("app.users") is table
    assert schema.get_table("users") is table


def test_get_table_by_model_def_checks_all_candidate_tables() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    schema.add_table(
        ModelDefinition(
            name="audit_logs",
            fields={"id": FieldDefinition("id", exp.DataType.build("int"))},
            kind=ModelKind.TABLE,
        )
    )
    schema.add_table(
        ModelDefinition(
            name="users",
            fields={
                "id": FieldDefinition("id", exp.DataType.build("int")),
                "email": FieldDefinition("email", exp.DataType.build("text")),
            },
            kind=ModelKind.TABLE,
        )
    )
    query_model = ModelDefinition(
        name="_override_me_",
        fields={
            "id": FieldDefinition(
                "id",
                exp.DataType.build("int"),
                column_ref=ColumnRef(name="id", table_name="users"),
            ),
            "email": FieldDefinition(
                "email",
                exp.DataType.build("text"),
                column_ref=ColumnRef(name="email", table_name="users"),
            ),
        },
    )

    matched = schema.get_table_by_model_def(query_model)

    assert matched is not None
    assert matched.name == "users"


def test_enum_and_composite_definitions_serialize() -> None:
    schema = DBSchema(dialect=Dialects.POSTGRES)
    schema.declare_catalog("app")
    schema.add_enum(
        EnumDefinition(
            name="status",
            catalog_name="app",
            values=[LiteralValue("active", quoted=True)],
        )
    )
    schema.add_composite_type(
        ModelDefinition(
            name="point_type",
            catalog_name="app",
            fields={"x": FieldDefinition("x", exp.DataType.build("int"))},
        )
    )

    dumped = schema.model_dump(exclude_none=True)

    assert dumped["catalogs"]["app"]["enums"]["status"]["values"] == [
        {"value": "active", "quoted": True}
    ]
    assert "x" in dumped["catalogs"]["app"]["composite_types"]["point_type"]["fields"]


def test_schema_parser_attaches_comments_to_catalog_objects_and_fields() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE TYPE app.status AS ENUM ('active', 'disabled');
    CREATE TYPE app.point_type AS (x integer, y integer);
    CREATE TABLE app.users (id integer, status app.status);
    COMMENT ON SCHEMA app IS 'Application schema';
    COMMENT ON TYPE app.status IS 'User status';
    COMMENT ON TABLE app.users IS 'User table';
    COMMENT ON COLUMN app.users.status IS 'Current user status';
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    assert schema.catalogs["app"].comment == "Application schema"
    assert schema.get_enum("status", "app").comment == "User status"
    assert [value.value for value in schema.get_enum("status", "app").values] == [
        "active",
        "disabled",
    ]
    assert "x" in schema.get_composite_type("point_type", "app").fields
    assert schema.get_table("users", "app").comment == "User table"
    assert schema.get_table("users", "app").fields["status"].comment == "Current user status"


def test_schema_parser_attaches_mysql_inline_comments() -> None:
    sql = """
    CREATE TABLE bar (
        baz text COMMENT "Column comment"
    ) COMMENT="Table comment";
    """

    schema = SchemaSqlParser(Dialects.MYSQL).parse_sql(sql)

    assert schema is not None
    table = schema.get_table("bar")
    assert table.comment == "Table comment"
    assert table.fields["baz"].comment == "Column comment"


def test_schema_parser_attaches_clickhouse_inline_comments() -> None:
    sql = """
    CREATE TABLE bar (
        baz String COMMENT 'Column comment'
    )
    ENGINE = Memory
    COMMENT 'Table comment';
    """

    schema = SchemaSqlParser(Dialects.CLICKHOUSE).parse_sql(sql)

    assert schema is not None
    table = schema.get_table("bar")
    assert table.comment == "Table comment"
    assert table.fields["baz"].comment == "Column comment"


def test_schema_parser_attaches_duckdb_comment_on_statements() -> None:
    sql = """
    CREATE TABLE bar (baz text);
    COMMENT ON TABLE bar IS 'Table comment';
    COMMENT ON COLUMN bar.baz IS 'Column comment';
    """

    schema = SchemaSqlParser(Dialects.DUCKDB).parse_sql(sql)

    assert schema is not None
    table = schema.get_table("bar")
    assert table.comment == "Table comment"
    assert table.fields["baz"].comment == "Column comment"


def test_schema_parser_rejects_undeclared_catalog() -> None:
    sql = """
    CREATE TYPE foo.point_type AS (x integer, y integer);
    """

    with pytest.raises(NormError) as exc_info:
        SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert exc_info.value.code == NormErrorCode.UNDECLARED_CATALOG


def test_schema_parser_resolves_composite_column_types() -> None:
    sql = """
    CREATE SCHEMA foo;

    CREATE TYPE point_type AS (x integer, y integer);
    CREATE TYPE foo.point_type AS (x integer, y integer);

    CREATE TABLE foo.paths (
        point_one point_type NOT NULL,
        point_two foo.point_type NOT NULL
    );
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    paths = schema.get_table("paths", "foo")
    public_point = schema.get_composite_type("point_type", "public")
    foo_point = schema.get_composite_type("point_type", "foo")

    assert paths.fields["point_one"].composite_type is public_point
    assert paths.fields["point_two"].composite_type is foo_point
    assert paths.fields["point_one"].column_ref.catalog_name == "foo"
    assert paths.fields["point_one"].sql_datatype is not None
    assert "composite_type" not in paths.fields["point_one"].model_dump(exclude_none=True)


def test_schema_parser_declares_catalog_from_create_schema() -> None:
    sql = "CREATE SCHEMA app;"

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    assert schema.catalogs["app"].declared is True
    assert schema.catalogs["app"].source == CatalogSource.DECLARED


def test_schema_parser_sqlite_accepts_typeless_columns() -> None:
    sql = "CREATE TABLE repro (id, name, seq);"

    schema = SchemaSqlParser(Dialects.SQLITE).parse_sql(sql)

    assert schema is not None
    table = schema.get_table("repro")
    assert table is not None
    assert set(table.fields) == {"id", "name", "seq"}
    for field in table.fields.values():
        assert field.sql_datatype is not None
        assert field.sql_datatype.is_type(exp.DataType.Type.UNKNOWN)


def test_schema_parser_postgres_ignores_typeless_columns() -> None:
    sql = "CREATE TABLE repro (id, name, seq);"

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    assert schema.get_table("repro") is None


def test_schema_parser_sqlite_table_constraint_does_not_shadow_columns() -> None:
    sql = """
    CREATE TABLE accounts (
        id TEXT NOT NULL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        UNIQUE (name COLLATE NOCASE)
    );
    """

    schema = SchemaSqlParser(Dialects.SQLITE).parse_sql(sql)

    assert schema is not None
    table = schema.get_table("accounts")
    assert table is not None
    assert table.fields["id"].sql_datatype.this == exp.DataType.Type.TEXT
    assert table.fields["name"].sql_datatype.this == exp.DataType.Type.TEXT


def test_schema_parser_parses_view_return_columns() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE VIEW app.v(x) AS SELECT 1 AS x;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    view = schema.get_view("v", "app")
    assert view is not None
    assert view.kind == ModelKind.VIEW
    assert set(view.fields) == {"x"}
    assert view.fields["x"].sql_datatype is not None
    assert view.fields["x"].sql_datatype.is_type(exp.DataType.Type.INT)


def test_schema_parser_infers_view_columns_from_select() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE TABLE app.users (id integer, name text);
    CREATE VIEW app.active_users AS SELECT id, name FROM app.users;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    view = schema.get_view("active_users", "app")
    assert view is not None
    assert set(view.fields) == {"id", "name"}
    assert view.fields["id"].sql_datatype is not None
    assert view.fields["id"].sql_datatype.is_type(exp.DataType.Type.INT)
    assert view.fields["name"].sql_datatype is not None
    assert view.fields["name"].sql_datatype.is_type(exp.DataType.Type.TEXT)


def test_schema_parser_parses_materialized_view() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE MATERIALIZED VIEW app.mv AS SELECT 1;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    view = schema.get_view("mv", "app")
    assert view is not None
    assert view.kind == ModelKind.MATERIALIZED_VIEW


def test_schema_parser_parses_function_parameters_and_table_return() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.f(a int) RETURNS TABLE(id int) LANGUAGE sql AS SELECT 1;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    function = schema.get_function("f", "app")
    assert function is not None
    assert set(function.parameters) == {"a"}
    assert function.parameters["a"].sql_datatype is not None
    assert function.parameters["a"].sql_datatype.is_type(exp.DataType.Type.INT)
    assert isinstance(function.return_type, ModelDefinition)
    assert "id" in function.return_type.fields
    assert function.return_type.fields["id"].sql_datatype is not None
    assert function.return_type.fields["id"].sql_datatype.is_type(exp.DataType.Type.INT)


def test_schema_parser_parses_function_scalar_return_type() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.f() RETURNS int LANGUAGE sql AS SELECT 1;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    function = schema.get_function("f", "app")
    assert function is not None
    assert isinstance(function.return_type, exp.DataType)
    assert function.return_type.is_type(exp.DataType.Type.INT)


def test_schema_parser_parses_duckdb_macro() -> None:
    sql = """
    CREATE MACRO add(a, b) AS a + b;
    CREATE MACRO main.typed(x INTEGER) AS x + 1;
    """

    schema = SchemaSqlParser(Dialects.DUCKDB).parse_sql(sql)

    assert schema is not None
    add = schema.get_function("add")
    assert add is not None
    assert add.kind == FunctionKind.MACRO
    assert set(add.parameters) == {"a", "b"}
    assert add.return_type is None

    typed = schema.get_function("typed", "main")
    assert typed is not None
    assert typed.kind == FunctionKind.MACRO
    assert typed.parameters["x"].sql_datatype is not None
    assert typed.parameters["x"].sql_datatype.is_type(exp.DataType.Type.INT)


def test_schema_parser_parses_clickhouse_function() -> None:
    sql = """
  CREATE FUNCTION add AS (a Int32, b Int32) -> a + b;
  CREATE FUNCTION mul AS (a Int32) -> Int32;
  """

    schema = SchemaSqlParser(Dialects.CLICKHOUSE).parse_sql(sql)

    assert schema is not None
    add = schema.get_function("add")
    assert add is not None
    assert add.kind == FunctionKind.FUNCTION
    assert set(add.parameters) == {"a", "b"}
    assert add.parameters["a"].sql_datatype is not None
    assert add.parameters["a"].sql_datatype.is_type(exp.DataType.Type.INT)

    mul = schema.get_function("mul")
    assert mul is not None
    assert mul.return_type is not None
    assert mul.return_type.is_type(exp.DataType.Type.INT)


def test_schema_parser_parses_mysql_function() -> None:
    sql = "CREATE FUNCTION f(i INT) RETURNS INT DETERMINISTIC RETURN i + 1;"

    schema = SchemaSqlParser(Dialects.MYSQL).parse_sql(sql)

    assert schema is not None
    function = schema.get_function("f")
    assert function is not None
    assert set(function.parameters) == {"i"}
    assert isinstance(function.return_type, exp.DataType)
    assert function.return_type.is_type(exp.DataType.Type.INT)


def test_schema_parser_attaches_comment_on_view() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE VIEW app.v AS SELECT 1;
    COMMENT ON VIEW app.v IS 'View comment';
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    view = schema.get_view("v", "app")
    assert view is not None
    assert view.comment == "View comment"
    assert schema.get_table("v", "app") is None


def test_schema_parser_skips_unparsed_function_ddl() -> None:
    sql = """
    CREATE TABLE t (id int);
    CREATE FUNCTION add(a int, b int) RETURNS int IMMUTABLE PARALLEL SAFE AS SELECT a + b;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    assert schema.get_table("t") is not None
    assert schema.get_function("add") is None


def test_schema_parser_allows_function_overloads_by_arg_type() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.foo(bar text) RETURNS bool LANGUAGE sql AS $$ SELECT true $$;
    CREATE FUNCTION app.foo(bar integer) RETURNS text LANGUAGE sql AS $$ SELECT 'baz' $$;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    overloads = schema.get_functions("foo", "app")
    assert len(overloads) == 2
    signatures = {
        function_signature_key(overload, dialect=Dialects.POSTGRES)
        for overload in overloads
    }
    assert signatures == {"text", "int"}


def test_schema_parser_allows_function_overloads_by_arity() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.foo(bar text) RETURNS bool LANGUAGE sql AS $$ SELECT true $$;
    CREATE FUNCTION app.foo(bar text, baz text) RETURNS text LANGUAGE sql AS $$ SELECT baz $$;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    overloads = schema.get_functions("foo", "app")
    assert len(overloads) == 2
    signatures = {
        function_signature_key(overload, dialect=Dialects.POSTGRES)
        for overload in overloads
    }
    assert signatures == {"text", "text,text"}


def test_schema_parser_rejects_duplicate_function_signature() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.foo(bar text) RETURNS bool LANGUAGE sql AS $$ SELECT true $$;
    CREATE FUNCTION app.foo(bar text) RETURNS text LANGUAGE sql AS $$ SELECT 'baz' $$;
    """

    with pytest.raises(NormError) as exc_info:
        SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert exc_info.value.code == NormErrorCode.DUPLICATE_FUNCTION


def test_schema_parser_function_parameters_inferred_without_cast() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.add(a int, b int) RETURNS int LANGUAGE sql AS SELECT 1;
    """

    schema_sql = """-- repo_name: Repo
-- name: CallAdd :one
SELECT app.add(:a, :b);
"""

    from norm.parsing import RepoSqlParser
    from norm.processing import QueryProcessor

    db_schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)
    repo = RepoSqlParser(Dialects.POSTGRES).parse_sql(schema_sql)
    assert db_schema is not None and repo is not None

    processed = QueryProcessor(db_schema).process(repo.queries[0])
    assert processed.parameters["a"].sql_datatype.is_type(exp.DataType.Type.INT)
    assert processed.parameters["b"].sql_datatype.is_type(exp.DataType.Type.INT)


def test_schema_parser_get_function_requires_signature_when_overloaded() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE FUNCTION app.foo(bar text) RETURNS bool LANGUAGE sql AS $$ SELECT true $$;
    CREATE FUNCTION app.foo(bar integer) RETURNS text LANGUAGE sql AS $$ SELECT 'baz' $$;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    assert schema.get_function("foo", "app") is None
    text_overload = schema.get_function("foo", "app", signature="text")
    int_overload = schema.get_function("foo", "app", signature="int")
    assert text_overload is not None
    assert int_overload is not None
    assert isinstance(text_overload.return_type, exp.DataType)
    assert text_overload.return_type.is_type(exp.DataType.Type.BOOLEAN)
    assert isinstance(int_overload.return_type, exp.DataType)
    assert int_overload.return_type.is_type(exp.DataType.Type.TEXT)


def test_schema_parser_rejects_duplicate_view() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE VIEW app.v AS SELECT 1;
    CREATE VIEW app.v AS SELECT 2;
    """

    with pytest.raises(NormError) as exc_info:
        SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert exc_info.value.code == NormErrorCode.DUPLICATE_VIEW


def test_schema_parser_serializes_views_and_functions() -> None:
    sql = """
    CREATE SCHEMA app;
    CREATE VIEW app.v(x) AS SELECT 1;
    CREATE FUNCTION app.f(a int) RETURNS int LANGUAGE sql AS SELECT 1;
    """

    schema = SchemaSqlParser(Dialects.POSTGRES).parse_sql(sql)

    assert schema is not None
    dumped = schema.model_dump(exclude_none=True)
    assert "x" in dumped["catalogs"]["app"]["views"]["v"]["fields"]
    function_overloads = dumped["catalogs"]["app"]["functions"]["f"]
    assert "int" in function_overloads
    assert "a" in function_overloads["int"]["parameters"]
    assert "return_type" in function_overloads["int"]
