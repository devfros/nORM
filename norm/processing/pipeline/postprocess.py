from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import exp

from norm.consts import TEMP_PLACEHOLDER_PATTERN, MetaKeys
from norm.processing.extracting import get_projection_expressions

if TYPE_CHECKING:
    from .context import ProcessingContext


class PostprocessStage:
    def __init__(self, context: ProcessingContext) -> None:
        self.context = context

    def lists(self, query: exp.Expr) -> exp.Expr:
        """
        Replace lists placeholders with temporary key for runtime replacement.
        """
        for ph in query.find_all(exp.Placeholder):
            key = ph.meta.get(MetaKeys.LIST_KEY)
            if key:
                list_key = TEMP_PLACEHOLDER_PATTERN.format(key)
                ph.replace(exp.Identifier(this=list_key))

        return query

    def placeholders(self, query: exp.Expr) -> exp.Expr:
        """
        Replace placeholders with dialect compatible ones.
        """
        for ph in query.find_all(exp.Placeholder):
            ph.replace(exp.Identifier(this=self.context.param_template.format(ph.name)))

        return query

    def projections(self, query: exp.Expr) -> exp.Expr:
        """
        Remove temporary projections.
        """
        if isinstance(query, exp.Update):
            return query

        projections = get_projection_expressions(query)
        if len(projections) == 0:
            return query

        new_projections = []
        for projection in projections:
            if MetaKeys.EMBED not in projection.meta:
                new_projections.append(projection)

        query.set("expressions", new_projections)

        return query
