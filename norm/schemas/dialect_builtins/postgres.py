from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import Dialects, exp

from norm.parsing.dialect_capabilities import supports_sql_builtins

if TYPE_CHECKING:
    from collections.abc import Callable

    from norm.schemas.parsing import FieldDefinition, ModelDefinition

CatalogTableKey = tuple[str, str]
_QUALIFIED_TABLE_PARTS = 2

POSTGRES_SYSTEM_COLUMNS: dict[str, str] = {
    "tableoid": "OID",
    "xmin": "xid",
    "cmin": "cid",
    "xmax": "xid",
    "cmax": "cid",
    "ctid": "tid",
}

POSTGRES_CATALOG_TABLES: dict[CatalogTableKey, dict[str, str]] = {
    ("pg_catalog", "pg_timezone_names"): {
        "name": "TEXT",
        "abbrev": "TEXT",
        "utc_offset": "INTERVAL",
        "is_dst": "BOOLEAN",
    },
}


def postgres_builtin_field(
    *,
    table_name: str,
    column_name: str,
    catalog_name: str | None = None,
    user_table: ModelDefinition | None = None,
    dialect: Dialects,
) -> FieldDefinition | None:
    if not supports_sql_builtins(dialect):
        return None

    catalog, resolved_table = _resolve_catalog_table(table_name, catalog_name)
    field = _catalog_field(catalog, resolved_table, column_name, dialect)
    if field:
        return field

    if user_table is not None:
        return _system_field(resolved_table, column_name, dialect)

    return None


def merge_postgres_builtin_schema_map(
    schema_map: dict,
    *,
    dialect: Dialects,
    identifier_aliases: Callable[[str], tuple[str, ...]],
) -> None:
    if not supports_sql_builtins(dialect):
        return

    for (catalog_name, table_name), columns in POSTGRES_CATALOG_TABLES.items():
        for catalog_alias in identifier_aliases(catalog_name):
            catalog_map = schema_map.setdefault(catalog_alias, {})
            for table_alias in identifier_aliases(table_name):
                table_map = catalog_map.setdefault(table_alias, {})
                for column_name, sql_type in columns.items():
                    dtype = _mapping_dtype(
                        catalog_name=catalog_name,
                        table_name=table_name,
                        sql_type=sql_type,
                        dialect=dialect,
                    )
                    for field_alias in identifier_aliases(column_name):
                        table_map.setdefault(field_alias, dtype)


def _catalog_field(
    catalog_name: str | None,
    table_name: str,
    column_name: str,
    dialect: Dialects,
) -> FieldDefinition | None:
    if not catalog_name:
        return None

    columns = POSTGRES_CATALOG_TABLES.get((catalog_name, table_name))
    if not columns:
        return None

    sql_type = columns.get(column_name)
    if not sql_type:
        for candidate, candidate_type in columns.items():
            if candidate.lower() == column_name.lower():
                sql_type = candidate_type
                column_name = candidate
                break

    if not sql_type:
        return None

    return _field_definition(
        catalog_name=catalog_name,
        table_name=table_name,
        column_name=column_name,
        sql_type=sql_type,
        dialect=dialect,
    )


def _system_field(
    table_name: str,
    column_name: str,
    dialect: Dialects,
) -> FieldDefinition | None:
    sql_type = POSTGRES_SYSTEM_COLUMNS.get(column_name)
    if not sql_type:
        for candidate, candidate_type in POSTGRES_SYSTEM_COLUMNS.items():
            if candidate.lower() == column_name.lower():
                sql_type = candidate_type
                column_name = candidate
                break

    if not sql_type:
        return None

    return _field_definition(
        table_name=table_name,
        column_name=column_name,
        sql_type=sql_type,
        dialect=dialect,
    )


def _field_definition(
    *,
    catalog_name: str | None = None,
    table_name: str,
    column_name: str,
    sql_type: str,
    dialect: Dialects,
) -> FieldDefinition:
    from norm.schemas.parsing import ColumnRef, FieldDefinition

    return FieldDefinition(
        name=column_name,
        datatype=exp.DataType.build(sql_type, dialect=dialect, udt=True),
        column_ref=ColumnRef(
            name=column_name,
            catalog_name=catalog_name,
            table_name=table_name,
        ),
    )


def _mapping_dtype(
    *,
    catalog_name: str,
    table_name: str,
    sql_type: str,
    dialect: Dialects,
) -> exp.DataType:
    from norm.consts import MetaKeys

    dtype = exp.DataType.build(sql_type, dialect=dialect, udt=True)
    dtype.meta[MetaKeys.CATALOG_NAME] = catalog_name
    dtype.meta[MetaKeys.TABLE_NAME] = table_name
    return dtype


def _resolve_catalog_table(
    table_name: str,
    catalog_name: str | None,
) -> tuple[str | None, str]:
    if catalog_name:
        return catalog_name, table_name

    parts = table_name.split(".", maxsplit=1)
    if len(parts) == _QUALIFIED_TABLE_PARTS:
        return parts[0], parts[1]

    return None, table_name
