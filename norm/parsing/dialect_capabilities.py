from sqlglot import Dialects

_TYPELESS_COLUMN_DIALECTS = frozenset({Dialects.SQLITE})
_SQL_BUILTINS_DIALECTS = frozenset({Dialects.POSTGRES})


def allows_typeless_columns(dialect: Dialects) -> bool:
    """Whether CREATE TABLE may declare columns without an explicit SQL type."""
    return dialect in _TYPELESS_COLUMN_DIALECTS


def supports_sql_builtins(dialect: Dialects) -> bool:
    """Whether dialect-specific catalog tables and system columns are available."""
    return dialect in _SQL_BUILTINS_DIALECTS
