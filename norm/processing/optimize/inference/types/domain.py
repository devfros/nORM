from __future__ import annotations

import typing as t
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlglot import Dialects, Schema, exp

from norm.processing.optimize.inference.ast_helpers import (
    contains_node,
    direct_child_expressions,
)

if TYPE_CHECKING:
    from norm.schemas.parsing import DBSchema


@dataclass(frozen=True)
class TypeConstraint:
    dtype: exp.DataType
    source: str
    priority: int
    terminal: bool = False


@dataclass(frozen=True)
class PlaceholderTypeContext:
    placeholder: exp.Placeholder
    current: exp.Expr
    parent: exp.Expr
    schema: Schema
    dialect: Dialects
    db_schema: DBSchema | None = None

    def type_of(self, expression: exp.Expr | None) -> exp.DataType | None:
        return type_of_expression(expression)

    def sibling_type(self) -> exp.DataType | None:
        return merged_type(
            self.type_of(expr)
            for expr in direct_child_expressions(self.parent)
            if not contains_node(expr, self.placeholder)
        )

    def child_type(self, arg_key: str) -> exp.DataType | None:
        value = self.parent.args.get(arg_key)
        if isinstance(value, exp.Expr):
            return self.type_of(value)
        return None


class Priority:
    DML = 90
    FUNCTION = 85
    COMPARISON = 80
    ARITHMETIC = 60
    STRUCTURAL = 50
    SOFT = 10


def constraint(
    dtype: exp.DataType | None,
    source: str,
    priority: int,
    *,
    terminal: bool = False,
) -> list[TypeConstraint]:
    return (
        [
            TypeConstraint(
                dtype=dtype,
                source=source,
                priority=priority,
                terminal=terminal,
            )
        ]
        if dtype
        else []
    )


def resolve_constraints(constraints: list[TypeConstraint]) -> exp.DataType | None:
    if not constraints:
        return None

    highest = max(item.priority for item in constraints)
    return merged_type(item.dtype for item in constraints if item.priority == highest)


def type_of_expression(expression: exp.Expr | None) -> exp.DataType | None:
    if expression is None:
        return None

    dtype = known_type(expression.type)
    if dtype:
        return dtype

    if isinstance(expression, exp.Literal):
        if expression.is_string:
            return data_type(exp.DType.TEXT)
        if expression.is_number:
            number = str(expression.this).upper()
            if "." in number or "E" in number:
                return data_type(exp.DType.FLOAT)
            return data_type(exp.DType.INT)

    if isinstance(expression, exp.Boolean):
        return data_type(exp.DType.BOOLEAN)

    return None


def merged_type(types: t.Iterable[exp.DataType | None]) -> exp.DataType | None:
    known = [dtype for dtype in types if known_type(dtype)]
    if not known:
        return None

    bases = {dtype_value(dtype) for dtype in known}
    if len(bases) == 1:
        return known[0]

    if bases <= exp.DataType.NUMERIC_TYPES:
        return data_type(exp.DType.DECIMAL)

    return None


def known_type(dtype: exp.DataType | None) -> exp.DataType | None:
    if dtype is None or dtype.is_type(exp.DType.UNKNOWN, exp.DType.NULL):
        return None
    return dtype


def dtype_value(dtype: exp.DataType) -> exp.DType:
    return dtype.this


def data_type(dtype: exp.DType) -> exp.DataType:
    return dtype.into_expr()


def cast_target_type(cast: exp.Cast) -> exp.DataType | None:
    target = cast.args.get("to")
    if isinstance(target, exp.DataType):
        return target
    return None
