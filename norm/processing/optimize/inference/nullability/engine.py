from __future__ import annotations

from sqlglot import Dialects, Schema, exp
from sqlglot.schema import ensure_schema

from norm.consts import MetaKeys
from norm.processing.optimize.inference.engine import (
    RuleRegistry,
    infer_placeholder_value,
)
from norm.processing.optimize.inference.nullability.domain import (
    PlaceholderNullabilityContext,
    resolve_constraints,
)
from norm.processing.optimize.inference.nullability.rules import (
    PLACEHOLDER_NULLABILITY_RULES,
)


def infer_placeholder_nullability(
    expression: exp.Expr,
    schema: Schema,
    dialect: Dialects,
) -> exp.Expr:
    schema = ensure_schema(schema, dialect=dialect)
    rules = RuleRegistry(PLACEHOLDER_NULLABILITY_RULES)

    for placeholder in expression.find_all(exp.Placeholder):
        inferred = infer_placeholder_value(
            placeholder,
            build_context=lambda current,
            parent,
            placeholder=placeholder: PlaceholderNullabilityContext(
                placeholder=placeholder,
                current=current,
                parent=parent,
                schema=schema,
                dialect=dialect,
            ),
            rules=rules,
            resolve_constraints=resolve_constraints,
            is_terminal=lambda item: item.terminal,
        )
        if inferred is not None and MetaKeys.NULLABLE not in placeholder.meta:
            placeholder.meta[MetaKeys.NULLABLE] = inferred

    return expression
