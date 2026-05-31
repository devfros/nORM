from __future__ import annotations

import typing as t
from dataclasses import dataclass

from sqlglot import Dialects, Schema, exp

from norm.consts import MetaKeys


@dataclass(frozen=True)
class NullabilityConstraint:
    nullable: bool
    source: str
    priority: int
    terminal: bool = False


@dataclass(frozen=True)
class PlaceholderNullabilityContext:
    placeholder: exp.Placeholder
    current: exp.Expr
    parent: exp.Expr
    schema: Schema
    dialect: Dialects

    def nullability_of(self, expression: exp.Expr | None) -> bool | None:
        return nullability_of_expression(expression)


class Priority:
    EXPLICIT = 100
    DML = 90
    FUNCTION = 80


def constraint(
    nullable: bool | None,
    source: str,
    priority: int,
    *,
    terminal: bool = False,
) -> list[NullabilityConstraint]:
    return (
        [
            NullabilityConstraint(
                nullable=nullable,
                source=source,
                priority=priority,
                terminal=terminal,
            )
        ]
        if nullable is not None
        else []
    )


def resolve_constraints(constraints: list[NullabilityConstraint]) -> bool | None:
    if not constraints:
        return None

    highest = max(item.priority for item in constraints)
    values = {item.nullable for item in constraints if item.priority == highest}
    return values.pop() if len(values) == 1 else None


def nullability_of_expression(expression: exp.Expr | None) -> bool | None:
    if expression is None:
        return None

    if MetaKeys.NULLABLE in expression.meta:
        return bool(expression.meta[MetaKeys.NULLABLE])

    if isinstance(expression, exp.Null):
        return True

    if isinstance(expression, (exp.Boolean, exp.Literal)):
        return False

    return nullable_from_type(expression.type)


def nullable_from_type(dtype: exp.DataType | None) -> bool | None:
    nullable = None
    if isinstance(dtype, exp.DataType) and MetaKeys.NULLABLE in dtype.meta:
        nullable = bool(dtype.meta[MetaKeys.NULLABLE])

    if dtype:
        nullable = dtype.args.get("nullable", nullable)

    return nullable


def merged_nullability(values: t.Iterable[bool | None]) -> bool | None:
    known = [value for value in values if value is not None]
    if not known:
        return None
    return any(known)
