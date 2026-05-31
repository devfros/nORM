from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.nullability.rules.conditionals import (
    case_rule,
    if_rule,
)
from norm.processing.optimize.inference.nullability.rules.dml import (
    insert_tuple_rule,
    update_rule,
)
from norm.processing.optimize.inference.nullability.rules.functions import (
    nullable_function_rule,
)
from norm.processing.optimize.inference.nullability.rules.predicates import (
    is_null_rule,
)

PLACEHOLDER_NULLABILITY_RULES = {
    exp.Tuple: insert_tuple_rule,
    exp.If: if_rule,
    exp.Case: case_rule,
    exp.EQ: update_rule,
    exp.Is: is_null_rule,
    exp.Coalesce: nullable_function_rule,
    exp.Nullif: nullable_function_rule,
}

__all__ = ["PLACEHOLDER_NULLABILITY_RULES"]
