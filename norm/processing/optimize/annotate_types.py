from __future__ import annotations

from sqlglot import Dialects, Schema, exp
from sqlglot.schema import ensure_schema

from .custom_annotator import CustomTypeAnnotator


def type_annotator(
    schema: Schema, dialect: Dialects, overwrite_types: bool = True
) -> CustomTypeAnnotator:
    schema = ensure_schema(schema, dialect=dialect)

    return CustomTypeAnnotator(
        schema=schema,
        expression_metadata={
            **{expr_type: {"returns": exp.DType.NULL} for expr_type in {exp.Null}},
            **{
                expr_type: {"returns": exp.DType.BIGINT}
                for expr_type in {
                    exp.ByteLength,
                    exp.DenseRank,
                    exp.Grouping,
                    exp.Length,
                    exp.Ntile,
                    exp.Rank,
                    exp.RowNumber,
                }
            },
            **{
                expr_type: {"returns": exp.DType.INT}
                for expr_type in {
                    exp.Floor,
                    exp.WidthBucket,
                }
            },
            **{
                expr_type: {"returns": exp.DType.DOUBLE}
                for expr_type in {
                    exp.Trunc,
                }
            },
            **schema.dialect.EXPRESSION_METADATA,
            **{
                expr_type: {"returns": exp.DType.TIMESTAMPTZ}
                for expr_type in {
                    exp.AtTimeZone,
                    exp.CurrentTimestamp,
                }
            },
            exp.Anonymous: {"annotator": _annotate_anonymous},
            exp.JSONExtractScalar: {"annotator": _annotate_json_extract_scalar},
            exp.Nullif: {"annotator": _annotate_nullif},
            exp.WithinGroup: {"annotator": _annotate_within_group},
        },
        coerces_to=None,
        overwrite_types=overwrite_types,
    )


def annotate_types(expression: exp.Expr, schema: Schema, dialect: Dialects) -> exp.Expr:
    return type_annotator(
        schema,
        dialect,
    ).annotate(expression)


_POSTGRES_FUNCTION_TYPES: dict[str, exp.DType] = {
    "jsonb_agg": exp.DType.JSONB,
    "jsonb_extract_path": exp.DType.JSONB,
    "nextval": exp.DType.BIGINT,
    "pg_advisory_unlock": exp.DType.BOOLEAN,
    "scale": exp.DType.INT,
    "similarity": exp.DType.FLOAT,
    "ts_rank": exp.DType.FLOAT,
}

_POSTGRES_SEMANTIC_FUNCTION_TYPES: dict[str, str] = {
    "json_build_object": "JSONOBJECT",
    "jsonb_build_object": "JSONOBJECT",
    "json_build_array": "JSONARRAY",
    "jsonb_build_array": "JSONARRAY",
}

_POSTGRES_VOID_FUNCTIONS: frozenset[str] = frozenset(
    {
        "pg_advisory_lock",
    }
)


def _user_defined_type(name: str) -> exp.DataType:
    return exp.DataType(
        this=exp.DType.USERDEFINED,
        kind=exp.Identifier(this=name),
    )


_VOID_DATATYPE = _user_defined_type("VOID")


def _annotate_anonymous(
    annotator: CustomTypeAnnotator,
    expression: exp.Anonymous,
) -> None:
    function_name = str(expression.name).lower()
    if function_name in _POSTGRES_VOID_FUNCTIONS:
        annotator.set_type(expression, _VOID_DATATYPE)
        return

    semantic_type = _POSTGRES_SEMANTIC_FUNCTION_TYPES.get(function_name)
    if semantic_type:
        annotator.set_type(expression, _user_defined_type(semantic_type))
        return

    annotator.set_type(expression, _POSTGRES_FUNCTION_TYPES.get(function_name))


def _annotate_json_extract_scalar(
    annotator: CustomTypeAnnotator,
    expression: exp.JSONExtractScalar,
) -> None:
    annotator.set_type(expression, exp.DType.TEXT)


def _annotate_nullif(
    annotator: CustomTypeAnnotator,
    expression: exp.Nullif,
) -> None:
    annotator.set_type(expression, expression.this.type)


def _annotate_within_group(
    annotator: CustomTypeAnnotator,
    expression: exp.WithinGroup,
) -> None:
    if not isinstance(expression.this, exp.PercentileDisc):
        annotator.set_type(expression, None)
        return

    order = expression.args.get("expression")
    if not isinstance(order, exp.Order):
        annotator.set_type(expression, None)
        return

    for ordered in order.expressions:
        if isinstance(ordered, exp.Ordered) and ordered.this.type:
            annotator.set_type(expression, ordered.this.type)
            return

    annotator.set_type(expression, None)
