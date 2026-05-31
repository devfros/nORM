from __future__ import annotations

from sqlglot import Dialects

CASE_INSENSITIVE_IDENTIFIER_DIALECTS = {
    Dialects.POSTGRES,
    Dialects.SQLITE,
    Dialects.MYSQL,
    Dialects.CLICKHOUSE,
    Dialects.DUCKDB,
}

QUOTED_CASE_INSENSITIVE_IDENTIFIER_DIALECTS = {
    Dialects.SQLITE,
    Dialects.DUCKDB,
}


def identifier_aliases(
    name: str,
    dialect: Dialects,
    *,
    quoted: bool = False,
) -> tuple[str, ...]:
    aliases = [name]

    should_fold = dialect in CASE_INSENSITIVE_IDENTIFIER_DIALECTS and (
        not quoted or dialect in QUOTED_CASE_INSENSITIVE_IDENTIFIER_DIALECTS
    )

    if should_fold:
        folded = name.lower()
        if folded not in aliases:
            aliases.append(folded)

    return tuple(aliases)
