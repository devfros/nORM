from __future__ import annotations

from sqlglot import exp

from norm.processing.optimize.inference.types.domain import Priority
from norm.processing.optimize.inference.types.rules.builders import fixed_rule
from norm.processing.optimize.inference.types.rules.conditionals import (
    case_rule,
    if_rule,
)
from norm.processing.optimize.inference.types.rules.dml import insert_tuple_rule
from norm.processing.optimize.inference.types.rules.functions import (
    function_signature_rule,
)
from norm.processing.optimize.inference.types.rules.operators import (
    ARITHMETIC_RULES,
    COMPARISON_RULES,
    CONCAT_RULES,
)
from norm.processing.optimize.inference.types.rules.predicates import (
    between_rule,
    cast_rule,
    in_rule,
    is_rule,
    logical_rule,
    not_rule,
    predicate_container_rule,
)

PLACEHOLDER_TYPE_RULES = {
    exp.Cast: cast_rule,
    exp.Tuple: insert_tuple_rule,
    exp.If: if_rule,
    exp.Case: case_rule,
    exp.And: logical_rule,
    exp.Or: logical_rule,
    exp.Not: not_rule,
    exp.Where: predicate_container_rule,
    exp.Having: predicate_container_rule,
    exp.Limit: fixed_rule(exp.DType.INT, source="limit_offset"),
    exp.Offset: fixed_rule(exp.DType.INT, source="limit_offset"),
    exp.Is: is_rule,
    exp.In: in_rule,
    exp.Between: between_rule,
    exp.Func: function_signature_rule,
    **COMPARISON_RULES,
    **ARITHMETIC_RULES,
    **CONCAT_RULES,
}

__all__ = ["PLACEHOLDER_TYPE_RULES", "Priority"]
