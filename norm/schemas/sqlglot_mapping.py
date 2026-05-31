from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import MappingSchema, exp

from norm.consts import MetaKeys
from norm.schemas.dialect_builtins.postgres import merge_postgres_builtin_schema_map
from norm.schemas.identifiers import identifier_aliases

if TYPE_CHECKING:
    from norm.schemas.parsing import DBSchema, FieldDefinition


def build_mapping_schema(db_schema: DBSchema) -> MappingSchema:
    schema_map = build_schema_mapping(db_schema)
    return MappingSchema(schema_map, dialect=db_schema.dialect, normalize=False)


def build_schema_mapping(db_schema: DBSchema) -> dict:
    schema_map = {}
    for catalog in db_schema.catalogs.values():
        catalog_map = {}

        for model in (
            *catalog.tables.values(),
            *catalog.views.values(),
        ):
            table_map = {}

            for field_item in model.fields.values():
                dtype = _mapping_dtype(
                    field_item,
                    catalog_name=catalog.name,
                    table_name=model.name,
                )
                if not dtype:
                    continue

                for field_name in identifier_aliases(
                    field_item.name,
                    db_schema.dialect,
                    quoted=field_item.quoted,
                ):
                    table_map.setdefault(field_name, dtype)

            for model_name in identifier_aliases(
                model.name,
                db_schema.dialect,
                quoted=model.quoted,
            ):
                catalog_map.setdefault(model_name, table_map)

        if catalog_map:
            for catalog_name in identifier_aliases(
                catalog.name,
                db_schema.dialect,
                quoted=catalog.quoted,
            ):
                schema_map.setdefault(catalog_name, catalog_map)

    merge_postgres_builtin_schema_map(
        schema_map,
        dialect=db_schema.dialect,
        identifier_aliases=lambda name: identifier_aliases(name, db_schema.dialect),
    )

    return schema_map


def _mapping_dtype(
    field_item: FieldDefinition,
    *,
    catalog_name: str,
    table_name: str,
) -> exp.DataType | None:
    if not field_item.sql_datatype:
        return None

    dtype = field_item.sql_datatype.copy()
    dtype.meta[MetaKeys.CATALOG_NAME] = catalog_name
    dtype.meta[MetaKeys.TABLE_NAME] = table_name
    dtype.meta[MetaKeys.NULLABLE] = field_item.constraints.nullable
    return dtype
