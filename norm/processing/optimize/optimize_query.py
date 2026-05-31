from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlglot.errors import OptimizeError
from sqlglot.optimizer.optimizer import optimize

from .errors import raise_norm_optimize_error
from .inference.types.engine import infer_placeholder_types as infer_types
from .rules import RULES

if TYPE_CHECKING:
    from sqlglot import Dialects, MappingSchema, exp

    from norm.schemas.parsing import DBSchema


def optimize_query(
    query: exp.Expr,
    schema: MappingSchema,
    dialect: Dialects,
    *,
    db_schema: DBSchema | None = None,
) -> exp.Expr:

    rules: tuple = RULES
    if db_schema is not None:
        bound_infer_types = partial(infer_types, db_schema=db_schema)
        rules = tuple(
            bound_infer_types if rule is infer_types else rule for rule in RULES
        )

    try:
        optimized = optimize(
            query,
            schema=schema,
            dialect=dialect,
            sql=query.sql(dialect=dialect),
            rules=rules,
            expand_alias_refs=True,
            allow_partial_qualification=True,
            validate_qualify_columns=False,
            quote_identifiers=False,
            identify=False,
        )
        return optimized
    except OptimizeError as err:
        raise_norm_optimize_error(err, query)
