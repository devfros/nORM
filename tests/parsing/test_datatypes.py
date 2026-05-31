from sqlglot import exp

from norm.parsing.datatypes import (
    enumcolumn_datatype,
    enum_literals_from_datatype,
    is_inline_enumcolumn_type,
    normalize_enum_datatype,
)


def test_enum_literals_from_inline_enum():
    datatype = exp.DataType.build("ENUM('a', 'b')")
    literals = enum_literals_from_datatype(datatype)
    assert [str(item.this) for item in literals] == ["a", "b"]


def test_normalize_enum_datatype_produces_enumcolumn():
    datatype = exp.DataType.build("ENUM('ok')")
    normalized = normalize_enum_datatype(datatype)
    assert is_inline_enumcolumn_type(normalized)
    assert [str(item.this) for item in normalized.expressions] == ["ok"]


def test_normalize_enum_datatype_normalizes_array_element():
    inner = exp.DataType.build("ENUM('x', 'y')")
    array_type = exp.DataType(this=exp.DType.ARRAY, expressions=[inner])
    normalized = normalize_enum_datatype(array_type)
    inner_normalized = normalized.expressions[0]
    assert is_inline_enumcolumn_type(inner_normalized)


def test_enumcolumn_datatype_from_strings():
    datatype = enumcolumn_datatype(["id", "name"])
    assert is_inline_enumcolumn_type(datatype)
    assert [str(item.this) for item in datatype.expressions] == ["id", "name"]


def test_normalize_enum_datatype_repairs_sqlglot_kind_string():
    broken = exp.DataType(
        this=exp.DType.USERDEFINED,
        kind="ENUMCOLUMN('ok', 'removed')",
    )
    normalized = normalize_enum_datatype(broken)
    assert is_inline_enumcolumn_type(normalized)
    assert [str(item.this) for item in normalized.expressions] == ["ok", "removed"]

