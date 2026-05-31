from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import Dialects, exp
from sqlglot.expressions import DType

if TYPE_CHECKING:
    from norm.schemas.parsing import DBSchema, FunctionDefinition


def schema_function_call(
    expression: exp.Expr,
) -> tuple[str | None, str | None, list[exp.Expr]]:
    if isinstance(expression, exp.Dot) and isinstance(
        expression.expression, exp.Anonymous
    ):
        catalog_name = (
            expression.this.name
            if isinstance(expression.this, exp.Identifier)
            else str(expression.this)
        )
        return (
            catalog_name,
            str(expression.expression.name),
            list(expression.expression.expressions or []),
        )

    if isinstance(expression, exp.Anonymous):
        return None, str(expression.name), list(expression.expressions or [])

    return None, None, []


def enclosing_schema_function_call(
    expression: exp.Expr,
) -> tuple[str | None, str | None, list[exp.Expr]]:
    node: exp.Expr | None = expression
    while node is not None:
        if isinstance(node, exp.Dot) and isinstance(node.expression, exp.Anonymous):
            return schema_function_call(node)
        if isinstance(node, exp.Anonymous):
            catalog_name = None
            parent = node.parent
            if isinstance(parent, exp.Dot) and isinstance(parent.this, exp.Identifier):
                catalog_name = parent.this.name
            return catalog_name, str(node.name), list(node.expressions or [])
        node = node.parent

    return None, None, []


def signature_from_call_arguments(
    args: list[exp.Expr],
    *,
    dialect: Dialects,
) -> str | None:
    type_names: list[str] = []
    for arg in args:
        arg_type = argument_type_name(arg, dialect=dialect)
        if arg_type is None:
            return None
        type_names.append(arg_type)
    return ",".join(type_names)


def argument_type_name(arg: exp.Expr, *, dialect: Dialects) -> str | None:
    if isinstance(arg, exp.Cast) and isinstance(arg.to, exp.DataType):
        return arg.to.sql(dialect=dialect).lower()

    arg_type = arg.type
    if isinstance(arg_type, exp.DataType) and not arg_type.is_type(DType.UNKNOWN):
        return arg_type.sql(dialect=dialect).lower()

    return None


def resolve_schema_function(
    db_schema: DBSchema,
    function_name: str | None,
    catalog_name: str | None,
    args: list[exp.Expr],
) -> FunctionDefinition | None:
    if not function_name:
        return None

    signature = signature_from_call_arguments(args, dialect=db_schema.dialect)
    if signature is not None:
        resolved = db_schema.get_function(
            function_name,
            catalog_name,
            signature=signature,
        )
        if resolved is not None:
            return resolved

    overloads = db_schema.get_functions(function_name, catalog_name)
    if len(overloads) == 1:
        return overloads[0]

    return None


def positional_schema_parameter_types(
    function: FunctionDefinition,
) -> dict[int, exp.DataType]:
    result: dict[int, exp.DataType] = {}
    for index, field in enumerate(function.parameters.values()):
        sql_datatype = field.sql_datatype
        if sql_datatype is None or sql_datatype.is_type(DType.UNKNOWN):
            continue
        result[index] = sql_datatype.copy()
    return result
