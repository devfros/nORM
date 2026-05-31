from __future__ import annotations

import typing as t

from norm.processing.optimize.inference.ast_helpers import other_binary_side
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    Priority,
    TypeConstraint,
    constraint,
    data_type,
)


def fixed_rule(
    dtype: object,
    *,
    source: str,
    priority: int = Priority.STRUCTURAL,
    terminal: bool = True,
) -> t.Callable[[PlaceholderTypeContext], list[TypeConstraint]]:
    def infer(_ctx: PlaceholderTypeContext) -> list[TypeConstraint]:
        return constraint(
            data_type(dtype),
            source,
            priority,
            terminal=terminal,
        )

    return infer


def same_as_other_binary_side(
    *,
    source: str,
    priority: int,
    fallback: object | None = None,
    terminal: bool = True,
) -> t.Callable[[PlaceholderTypeContext], list[TypeConstraint]]:
    def infer(ctx: PlaceholderTypeContext) -> list[TypeConstraint]:
        other = other_binary_side(ctx.parent, ctx.placeholder)
        dtype = ctx.type_of(other)
        if dtype is None and fallback:
            dtype = data_type(fallback)
        return constraint(dtype, source, priority, terminal=terminal)

    return infer


def same_as_siblings(
    *,
    source: str,
    priority: int,
    fallback: object | None = None,
    terminal: bool = True,
) -> t.Callable[[PlaceholderTypeContext], list[TypeConstraint]]:
    def infer(ctx: PlaceholderTypeContext) -> list[TypeConstraint]:
        dtype = ctx.sibling_type()
        if dtype is None and fallback:
            dtype = data_type(fallback)
        return constraint(dtype, source, priority, terminal=terminal)

    return infer
