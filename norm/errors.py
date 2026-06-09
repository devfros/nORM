from dataclasses import dataclass
from enum import StrEnum


@dataclass
class InferenceIssue:
    kind: str
    placeholder: str
    context: str
    message: str


class NormErrorCode(StrEnum):
    INVALID_CONFIG = "INVALID_CONFIG"
    OUTOFDATE = "OUTOFDATE"
    OPTIMIZATION_ERROR = "OPTIMIZATION_ERROR"
    MISSING_ANNOTATION = "MISSING_ANNOTATION"
    INVALID_ANNOTATION = "INVALID_ANNOTATION"
    SQL_PARSE_FAILED = "SQL_PARSE_FAILED"
    DUPLICATE_QUERY = "DUPLICATE_QUERY"
    DUPLICATE_TABLE = "DUPLICATE_TABLE"
    DUPLICATE_VIEW = "DUPLICATE_VIEW"
    DUPLICATE_FUNCTION = "DUPLICATE_FUNCTION"
    DUPLICATE_PARAMETER = "DUPLICATE_PARAMETER"
    UNDECLARED_CATALOG = "UNDECLARED_CATALOG"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    CONFLICTING_CONSTRAINTS = "CONFLICTING_CONSTRAINTS"
    TYPE_INFERENCE_FAILED = "TYPE_INFERENCE_FAILED"
    UNKNOWN_TABLE_ALIAS = "UNKNOWN_TABLE_ALIAS"
    UNKNOWN_TABLE = "UNKNOWN_TABLE"
    UNKNOWN_COLUMN = "UNKNOWN_COLUMN"
    UNKNOWN_TARGET = "UNKNOWN_TARGET"
    AMBIGUOUS_COLUMN = "AMBIGUOUS_COLUMN"
    INVALID_MACRO_USAGE = "INVALID_MACRO_USAGE"
    INVALID_MACRO_TARGET = "INVALID_MACRO_TARGET"
    OUTPUT_SCHEMA_RESOLUTION_FAILED = "OUTPUT_SCHEMA_RESOLUTION_FAILED"
    INVALID_QUERY_COMMAND = "INVALID_QUERY_COMMAND"


class NormError(Exception):
    def __init__(
        self,
        code: NormErrorCode,
        message: str,
        *,
        hint: str | None = None,
        context: dict[str, object] | None = None,
    ):
        self.code = code
        self.message = message
        self.hint = hint
        self.context = context or {}
        super().__init__(f"[{code}] {message}")

    def to_display_lines(self) -> list[str]:
        from norm.cli.redact import redact_context

        lines = [f"[{self.code}] {self.message}"]
        if self.hint:
            lines.append(f"Hint: {self.hint}")
        if self.context:
            for key, value in redact_context(self.context).items():
                lines.append(f"{key}: {value}")
        return lines


def merge_context(
    err: NormError,
    extra: dict[str, object],
) -> dict[str, object]:
    merged = dict(err.context)
    merged.update(extra)
    return merged


def to_file_line(
    sql_start_line: int | None,
    query_line: int | None = None,
) -> int | None:
    if sql_start_line is None:
        return None
    if query_line is None:
        return sql_start_line
    return sql_start_line + query_line - 1


def with_context(err: NormError, **extra: object) -> NormError:
    return NormError(
        code=err.code,
        message=err.message,
        hint=err.hint,
        context=merge_context(err, extra),
    )


def unknown_table_alias(alias: str) -> NormError:
    return NormError(
        code=NormErrorCode.UNKNOWN_TABLE_ALIAS,
        message=(
            f"Unknown table alias '{alias}': "
            "no matching table or alias found in FROM/JOIN clauses"
        ),
        hint="Check aliases in FROM/JOIN and use the same alias in projections/macros.",
        context={"alias": alias},
    )


def unknown_table(table: str) -> NormError:
    return NormError(
        code=NormErrorCode.UNKNOWN_TABLE,
        message=f"Table '{table}' not found in schema",
        hint="Check that the table exists in your database schema.",
        context={"table": table},
    )


def unknown_column(column: str, table: str | None = None) -> NormError:
    if table:
        message = f"Column '{column}' not found in table '{table}'"
        hint = f"Check the schema for table '{table}' or fix the selected column name."
    else:
        message = f"Column '{column}' not found in any table in the query"
        hint = "Qualify the column with a table alias or fix the column name."
    return NormError(
        code=NormErrorCode.UNKNOWN_COLUMN,
        message=message,
        hint=hint,
        context={"column": column, "table": table},
    )


def ambiguous_column(column: str, tables: list[str]) -> NormError:
    return NormError(
        code=NormErrorCode.AMBIGUOUS_COLUMN,
        message=f"Column '{column}' is ambiguous - found in multiple tables: {', '.join(tables)}",
        hint="Qualify the column with a table alias, e.g., 'table_alias.column_name'.",
        context={"column": column, "tables": tables},
    )


def type_inference_failed(
    issues: list[InferenceIssue], query_info: str | None = None
) -> NormError:
    query_info = f" for query '{query_info}'" if query_info else ""
    context = {
        "query_info": query_info,
        "issues": [
            {
                "kind": item.kind,
                "placeholder": item.placeholder,
                "context": item.context,
                "message": item.message,
            }
            for item in issues
        ],
    }
    return NormError(
        code=NormErrorCode.TYPE_INFERENCE_FAILED,
        message=f"Type inference failed{query_info}",
        hint=(
            "Try explicit SQL casts or disambiguate columns/aliases "
            "to make parameter types deterministic."
        ),
        context=context,
    )
