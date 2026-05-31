from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import exp

from norm.parsing.datatypes import is_inline_enumcolumn_type
from norm.schemas.parsing import (
    DBSchema,
    EnumDefinition,
    FieldDefinition,
    FunctionDefinition,
    ModelDefinition,
)

if TYPE_CHECKING:
    from sqlglot.expressions import DataType

_QUALIFIED_TYPE_PARTS = 2


def user_defined_type_reference(
    datatype: DataType | None,
) -> tuple[str | None, str] | None:
    if datatype is None or datatype.this != exp.DType.USERDEFINED:
        return None

    kind = datatype.args.get("kind")
    if isinstance(kind, exp.Identifier):
        if is_inline_enumcolumn_type(datatype):
            return None
        return None, kind.name

    if isinstance(kind, str):
        parts = kind.split(".", maxsplit=1)
        if len(parts) == _QUALIFIED_TYPE_PARTS:
            return parts[0], parts[1]
        return None, kind

    if isinstance(kind, exp.Dot):
        catalog_expr = kind.this
        type_expr = kind.expression
        if isinstance(catalog_expr, exp.Identifier) and isinstance(
            type_expr, exp.Identifier
        ):
            return catalog_expr.name, type_expr.name

    return None


def resolve_schema_field_types(db_schema: DBSchema) -> None:
    for catalog in db_schema.catalogs.values():
        for table in catalog.tables.values():
            _resolve_fields_in_model(db_schema, table)

        for view in catalog.views.values():
            _resolve_fields_in_model(db_schema, view)

        for overloads in catalog.functions.values():
            for function in overloads.values():
                _resolve_parameters(db_schema, function)
                _resolve_function_return_type(db_schema, function)


def _resolve_fields_in_model(db_schema: DBSchema, model: ModelDefinition) -> None:
    for field in model.fields.values():
        _resolve_field(db_schema, field, model.catalog_name)


def _resolve_parameters(db_schema: DBSchema, function: FunctionDefinition) -> None:
    for field in function.parameters.values():
        _resolve_field(db_schema, field, function.catalog_name)


def _resolve_field(
    db_schema: DBSchema,
    field: FieldDefinition,
    object_catalog: str | None,
) -> None:
    composite = _resolve_composite_type(db_schema, field, object_catalog)
    if composite is not None:
        _link_field_to_composite(field, composite)

    enum = resolve_enum_type(db_schema, field.sql_datatype, object_catalog)
    if enum is not None:
        _link_field_to_enum(field, enum)


def _resolve_function_return_type(
    db_schema: DBSchema,
    function: FunctionDefinition,
) -> None:
    return_type = function.return_type
    if isinstance(return_type, ModelDefinition):
        _resolve_fields_in_model(db_schema, return_type)
        return

    if not isinstance(return_type, exp.DataType):
        return

    composite = _resolve_composite_type_for_datatype(
        db_schema,
        return_type,
        function.catalog_name,
    )
    if composite is not None:
        function.return_type = composite
        return

    enum = resolve_enum_type(db_schema, return_type, function.catalog_name)
    if enum is not None:
        return


def _resolve_composite_type_for_datatype(
    db_schema: DBSchema,
    datatype: DataType,
    object_catalog: str | None,
) -> ModelDefinition | None:
    reference = user_defined_type_reference(datatype)
    if reference is None:
        return None

    catalog_name, type_name = reference
    if catalog_name is not None:
        return db_schema.get_composite_type(type_name, catalog_name)

    composite = db_schema.get_composite_type(type_name, db_schema.default_catalog)
    if composite is not None:
        return composite

    return db_schema.get_composite_type(type_name, object_catalog)


def _resolve_composite_type(
    db_schema: DBSchema,
    field: FieldDefinition,
    table_catalog: str | None,
) -> ModelDefinition | None:
    reference = user_defined_type_reference(field.sql_datatype)
    if reference is None:
        return None

    catalog_name, type_name = reference
    if catalog_name is not None:
        return db_schema.get_composite_type(type_name, catalog_name)

    composite = db_schema.get_composite_type(type_name, db_schema.default_catalog)
    if composite is not None:
        return composite

    return db_schema.get_composite_type(type_name, table_catalog)


def resolve_enum_type(
    db_schema: DBSchema,
    datatype: DataType | None,
    table_catalog: str | None,
) -> EnumDefinition | None:
    reference = user_defined_type_reference(datatype)
    if reference is None:
        return None

    catalog_name, type_name = reference
    if catalog_name is not None:
        return db_schema.get_enum(type_name, catalog_name)

    enum = db_schema.get_enum(type_name, db_schema.default_catalog)
    if enum is not None:
        return enum

    return db_schema.get_enum(type_name, table_catalog)


def _link_field_to_composite(
    field: FieldDefinition, composite: ModelDefinition
) -> None:
    field.composite_type = composite


def _link_field_to_enum(field: FieldDefinition, enum: EnumDefinition) -> None:
    field.enum_type = enum
