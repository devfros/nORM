from __future__ import annotations

from sqlglot import exp

from norm.errors import NormError
from norm.processing.optimize import optimize_query
from norm.processing.processor import QueryProcessor
from norm.schemas.parsing import (
    Constraints,
    DBSchema,
    FieldDefinition,
    ModelDefinition,
)

_TYPELESS_COLUMN_TYPE = exp.DataType.build("UNKNOWN")


def populate_view_fields(
    view: ModelDefinition,
    query: exp.Expr | None,
    column_names: list[str],
    db_schema: DBSchema,
) -> None:
    if query is None:
        _apply_explicit_columns(view, column_names)
        return

    processor = QueryProcessor(db_schema)
    preprocessed = processor.preprocess(query)
    optimized = optimize_query(
        preprocessed,
        schema=db_schema.map(),
        dialect=db_schema.dialect,
        db_schema=db_schema,
    )

    try:
        inferred = processor.extract_return_fields(optimized)
    except NormError:
        _apply_explicit_columns(view, column_names)
        return

    if column_names:
        if len(column_names) != len(inferred):
            _apply_explicit_columns(view, column_names)
            return
        view.fields = {}
        for name, field in zip(column_names, inferred, strict=True):
            view.fields[name] = FieldDefinition(
                name=name,
                datatype=field.datatype,
                constraints=field.constraints,
                column_ref=field.column_ref,
                comment=field.comment,
                quoted=field.quoted,
            )
        return

    view.fields = {field.name: field for field in inferred}


def _apply_explicit_columns(view: ModelDefinition, column_names: list[str]) -> None:
    if not column_names:
        return
    for column_name in column_names:
        if column_name in view.fields:
            continue
        view.fields[column_name] = FieldDefinition(
            name=column_name,
            datatype=_TYPELESS_COLUMN_TYPE,
            constraints=Constraints(nullable=True),
        )
