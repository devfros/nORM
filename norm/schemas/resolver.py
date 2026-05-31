from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from norm.parsing.dialect_capabilities import supports_sql_builtins
from norm.schemas.dialect_builtins.postgres import postgres_builtin_field

if TYPE_CHECKING:
    from norm.schemas.parsing import (
        DBSchema,
        EnumDefinition,
        FieldDefinition,
        FunctionDefinition,
        ModelDefinition,
    )

_QUALIFIED_NAME_PARTS = 2
_LookupT = TypeVar("_LookupT")


class SchemaResolver:
    def __init__(self, db_schema: DBSchema) -> None:
        self.db_schema = db_schema

    def table(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        if not name:
            return None

        catalog, table_name = _split_qualified_name(name, catalog_name)
        if catalog:
            catalog_def = self.db_schema.catalogs.get(catalog)
            return catalog_def.tables.get(table_name) if catalog_def else None

        default = self.db_schema.catalogs.get(self.db_schema.default_catalog)
        if default and table_name in default.tables:
            return default.tables[table_name]

        matches = [
            catalog_def.tables[table_name]
            for catalog_def in self.db_schema.catalogs.values()
            if table_name in catalog_def.tables
        ]
        return matches[0] if len(matches) == 1 else None

    def field(
        self,
        column_name: str,
        table_name: str | None,
        catalog_name: str | None = None,
    ) -> FieldDefinition | None:
        if not table_name:
            return None

        table = self.table(table_name, catalog_name)
        if table:
            field = _field_in_model(table, column_name)
            if field:
                return field

        view = self.view(table_name, catalog_name)
        if view:
            field = _field_in_model(view, column_name)
            if field:
                return field

        if supports_sql_builtins(self.db_schema.dialect):
            return postgres_builtin_field(
                table_name=table_name,
                column_name=column_name,
                catalog_name=catalog_name,
                user_table=table,
                dialect=self.db_schema.dialect,
            )

        return None

    def enum(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> EnumDefinition | None:
        if not name:
            return None

        catalog, enum_name = _split_qualified_name(name, catalog_name)
        if catalog:
            catalog_def = self.db_schema.catalogs.get(catalog)
            return catalog_def.enums.get(enum_name) if catalog_def else None

        default = self.db_schema.catalogs.get(self.db_schema.default_catalog)
        if default and enum_name in default.enums:
            return default.enums[enum_name]

        matches = [
            catalog_def.enums[enum_name]
            for catalog_def in self.db_schema.catalogs.values()
            if enum_name in catalog_def.enums
        ]
        return matches[0] if len(matches) == 1 else None

    def composite_type(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        if not name:
            return None

        catalog, type_name = _split_qualified_name(name, catalog_name)
        if catalog:
            catalog_def = self.db_schema.catalogs.get(catalog)
            return catalog_def.composite_types.get(type_name) if catalog_def else None

        default = self.db_schema.catalogs.get(self.db_schema.default_catalog)
        if default and type_name in default.composite_types:
            return default.composite_types[type_name]

        matches = [
            catalog_def.composite_types[type_name]
            for catalog_def in self.db_schema.catalogs.values()
            if type_name in catalog_def.composite_types
        ]
        return matches[0] if len(matches) == 1 else None

    def view(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> ModelDefinition | None:
        return _lookup_named_object(
            self.db_schema,
            name,
            catalog_name,
            bucket="views",
        )

    def functions(
        self,
        name: str | None,
        catalog_name: str | None = None,
    ) -> list[FunctionDefinition]:
        overloads = _lookup_function_overloads(
            self.db_schema,
            name,
            catalog_name,
        )
        if overloads is None:
            return []
        return list(overloads.values())

    def function(
        self,
        name: str | None,
        catalog_name: str | None = None,
        *,
        signature: str | None = None,
    ) -> FunctionDefinition | None:
        overloads = _lookup_function_overloads(
            self.db_schema,
            name,
            catalog_name,
        )
        if overloads is None:
            return None

        if signature is not None:
            return overloads.get(signature)

        if len(overloads) == 1:
            return next(iter(overloads.values()))

        return None

    def table_by_model_def(self, model: ModelDefinition) -> ModelDefinition | None:
        for table in self.db_schema.tables.values():
            if len(model.fields) != len(table.fields):
                continue

            visited = set()
            matched = True

            for name, model_field in model.fields.items():
                source_column = (
                    model_field.column_ref.name if model_field.column_ref else None
                )
                if (
                    name in visited
                    or not model_field.column_ref
                    or model_field.column_ref.table_name != table.name
                    or (
                        model_field.column_ref.catalog_name is not None
                        and model_field.column_ref.catalog_name != table.catalog_name
                    )
                    or source_column not in table.fields
                    or name != source_column
                ):
                    matched = False
                    break

                visited.add(name)

            if matched:
                return table.model_copy(deep=True)

        return None


def _lookup_function_overloads(
    db_schema: DBSchema,
    name: str | None,
    catalog_name: str | None,
) -> dict[str, FunctionDefinition] | None:
    if not name:
        return None

    catalog, function_name = _split_qualified_name(name, catalog_name)
    if catalog:
        catalog_def = db_schema.catalogs.get(catalog)
        if not catalog_def:
            return None
        return catalog_def.functions.get(function_name)

    default = db_schema.catalogs.get(db_schema.default_catalog)
    if default and function_name in default.functions:
        return default.functions[function_name]

    matches = [
        catalog_def.functions[function_name]
        for catalog_def in db_schema.catalogs.values()
        if function_name in catalog_def.functions
    ]
    return matches[0] if len(matches) == 1 else None


def _lookup_named_object(
    db_schema: DBSchema,
    name: str | None,
    catalog_name: str | None,
    *,
    bucket: str,
) -> _LookupT | None:
    if not name:
        return None

    catalog, object_name = _split_qualified_name(name, catalog_name)
    if catalog:
        catalog_def = db_schema.catalogs.get(catalog)
        if not catalog_def:
            return None
        objects = getattr(catalog_def, bucket)
        return objects.get(object_name)

    default = db_schema.catalogs.get(db_schema.default_catalog)
    if default:
        objects = getattr(default, bucket)
        if object_name in objects:
            return objects[object_name]

    matches = [
        getattr(catalog_def, bucket)[object_name]
        for catalog_def in db_schema.catalogs.values()
        if object_name in getattr(catalog_def, bucket)
    ]
    return matches[0] if len(matches) == 1 else None


def _split_qualified_name(
    name: str,
    catalog_name: str | None = None,
) -> tuple[str | None, str]:
    if catalog_name:
        return catalog_name, name

    parts = name.split(".", maxsplit=1)
    if len(parts) == _QUALIFIED_NAME_PARTS:
        return parts[0], parts[1]

    return None, name


def _field_in_model(
    table: ModelDefinition,
    column_name: str,
) -> FieldDefinition | None:
    field = table.fields.get(column_name)
    if field:
        return field

    for candidate in table.fields.values():
        if _same_identifier(candidate.name, column_name):
            return candidate

    return None


def _same_identifier(left: str, right: str) -> bool:
    return left == right or left.lower() == right.lower()
