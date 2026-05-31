from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

ParentRule = Callable[[Any], list[Any]]


class RuleRegistry:
    def __init__(self, rules: Mapping[type[object], ParentRule]) -> None:
        self.rules = rules

    def get(self, expression: object) -> ParentRule | None:
        for cls in type(expression).__mro__:
            rule = self.rules.get(cls)
            if rule:
                return rule
        return None


def infer_placeholder_value(
    placeholder: Any,
    *,
    build_context: Callable[[Any, Any], Any],
    rules: RuleRegistry,
    resolve_constraints: Callable[[list[Any]], Any],
    is_terminal: Callable[[Any], bool],
) -> Any:
    constraints: list[Any] = []
    current = placeholder

    while current.parent:
        parent = current.parent
        context = build_context(current, parent)

        rule = rules.get(parent)
        if rule:
            new_constraints = rule(context)
            constraints.extend(new_constraints)
            if any(is_terminal(constraint) for constraint in new_constraints):
                break

        current = parent

    return resolve_constraints(constraints)
