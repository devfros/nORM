from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import Dialects, Schema, exp
from sqlglot.schema import ensure_schema

from norm.processing.optimize.annotate_types import type_annotator
from norm.processing.optimize.inference.engine import (
    RuleRegistry,
    infer_placeholder_value,
)
from norm.processing.optimize.inference.types.domain import (
    PlaceholderTypeContext,
    resolve_constraints,
)
from norm.processing.optimize.inference.types.rules import PLACEHOLDER_TYPE_RULES

if TYPE_CHECKING:
    from norm.schemas.parsing import DBSchema


def infer_placeholder_types(
    expression: exp.Expr,
    schema: Schema,
    dialect: Dialects,
    *,
    db_schema: DBSchema | None = None,
) -> exp.Expr:
    schema = ensure_schema(schema, dialect=dialect)
    annotator = type_annotator(schema, dialect)
    rules = RuleRegistry(PLACEHOLDER_TYPE_RULES)

    for placeholder in expression.find_all(exp.Placeholder):
        inferred = infer_placeholder_value(
            placeholder,
            build_context=lambda current,
            parent,
            placeholder=placeholder: PlaceholderTypeContext(
                placeholder=placeholder,
                current=current,
                parent=parent,
                schema=schema,
                dialect=dialect,
                db_schema=db_schema,
            ),
            rules=rules,
            resolve_constraints=resolve_constraints,
            is_terminal=lambda item: item.terminal,
        )
        if inferred:
            annotator.set_type(placeholder, inferred)

    return expression
