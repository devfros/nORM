from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlglot import exp

from norm.consts import TEMP_PLACEHOLDER_PATTERN
from norm.processing.dynamic_queries import get_filter_clauses, process_filter_clause

if TYPE_CHECKING:
    from .context import ProcessingContext

PostprocessFn = Callable[[exp.Expr], exp.Expr]


class DynamicFilterStage:
    def __init__(self, context: ProcessingContext) -> None:
        self.context = context

    def process(
        self,
        query: exp.Expr,
        with_postprocessing: bool = True,
        postprocess: PostprocessFn | None = None,
    ) -> exp.Expr:
        filter_clauses = get_filter_clauses(query)

        for num, clause in enumerate(filter_clauses):
            key = f"FILTER{num + 1}"
            dynamic_filter = process_filter_clause(
                clause,
                self.context.dialect,
                self.context.enforce_dynamic_filtering,
                postprocess if with_postprocessing else None,
            )

            if dynamic_filter:
                self.context.filters[key] = dynamic_filter
                clause.replace(
                    exp.Identifier(this=f" {TEMP_PLACEHOLDER_PATTERN.format(key)}")
                )

        return query
