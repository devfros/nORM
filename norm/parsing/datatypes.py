from __future__ import annotations

from typing import TYPE_CHECKING

from sqlglot import exp

if TYPE_CHECKING:
    from collections.abc import Iterable

# Synthetic USERDEFINED kind: closed set of column/parameter literals (not a DB enum type).
INLINE_ENUM_DATATYPE_KIND = "ENUMCOLUMN"

_INLINE_ENUM_DTYPES = {
    exp.DataType.Type.ENUM,
    exp.DataType.Type.ENUM8,
    exp.DataType.Type.ENUM16,
}


def enumcolumn_kind_name(kind: object) -> str | None:
    if isinstance(kind, exp.Identifier):
        return kind.name.upper()
    if isinstance(kind, str):
        name = kind.split("(", 1)[0].strip().upper()
        if name == INLINE_ENUM_DATATYPE_KIND:
            return name
    return None


def is_inline_enumcolumn_type(datatype: exp.DataType) -> bool:
    if datatype.this != exp.DType.USERDEFINED:
        return False
    if enumcolumn_kind_name(datatype.args.get("kind")) != INLINE_ENUM_DATATYPE_KIND:
        return False
    return bool(datatype.expressions)


def _repair_enumcolumn_datatype(datatype: exp.DataType) -> exp.DataType | None:
    kind = datatype.args.get("kind")
    if not isinstance(kind, str) or not kind.upper().startswith(
        INLINE_ENUM_DATATYPE_KIND
    ):
        return None

    open_paren = kind.find("(")
    if open_paren < 0:
        return None

    parsed_enum = exp.DataType.build(f"ENUM{kind[open_paren:]}", udt=True)
    literals = enum_literals_from_datatype(parsed_enum)
    if not literals:
        return None

    return enumcolumn_datatype(literals)


def enum_literals_from_datatype(datatype: exp.DataType) -> list[exp.Literal]:
    if datatype.this not in _INLINE_ENUM_DTYPES or not datatype.expressions:
        return []

    literals: list[exp.Literal] = []
    for expr in datatype.expressions:
        if isinstance(expr, exp.Literal):
            literals.append(expr)
        elif isinstance(expr, exp.EQ) and isinstance(expr.this, exp.Literal):
            literals.append(expr.this)
    return literals


def enumcolumn_datatype(values: Iterable[str | exp.Literal]) -> exp.DataType:
    literals: list[exp.Literal] = []
    for value in values:
        if isinstance(value, exp.Literal):
            literals.append(value)
        else:
            literals.append(exp.Literal(this=value, is_string=True))

    return exp.DataType(
        this=exp.DType.USERDEFINED,
        kind=exp.Identifier(this=INLINE_ENUM_DATATYPE_KIND),
        expressions=literals,
    )


def normalize_enum_datatype(datatype: exp.DataType) -> exp.DataType:
    if is_inline_enumcolumn_type(datatype):
        return datatype

    repaired = _repair_enumcolumn_datatype(datatype)
    if repaired is not None:
        return repaired

    literals = enum_literals_from_datatype(datatype)
    if literals:
        return enumcolumn_datatype(literals)

    if datatype.this == exp.DType.ARRAY and datatype.expressions:
        inner = datatype.expressions[0]
        if isinstance(inner, exp.DataType):
            normalized_inner = normalize_enum_datatype(inner)
            if normalized_inner is not inner:
                array_type = datatype.copy()
                array_type.set("expressions", [normalized_inner])
                return array_type

    return datatype
