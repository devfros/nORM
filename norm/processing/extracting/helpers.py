from sqlglot import Dialect, Dialects, Parser, TokenType, exp


def get_ordered_parameter_sequence(query: exp.Expr, dialect: Dialects) -> list[str]:
    result = []

    tokenizer = Dialect.get_or_raise(dialect).tokenizer()
    tokens = tokenizer.tokenize(query.sql())

    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        token_type = token.token_type

        if token_type == TokenType.COLON and idx + 1 < len(tokens):
            next_token = tokens[idx + 1]
            if next_token.token_type in Parser.COLON_PLACEHOLDER_TOKENS:
                result.append(next_token.text)
                idx += 2
                continue

        if token_type in set(Parser.PLACEHOLDER_PARSERS) - {TokenType.PARAMETER}:
            idx += 1
            continue
        idx += 1

    return result


def get_projection_expressions(query: exp.Expr) -> list[exp.Expr]:
    if isinstance(query, exp.Select):
        return query.expressions or []

    if isinstance(query, exp.Except):
        return get_projection_expressions(query.this)

    if isinstance(query, exp.Intersect):
        return get_projection_expressions(query.this)

    if isinstance(query, exp.Union):
        return get_projection_expressions(query.this)

    returning = query.args.get("returning")
    if isinstance(returning, exp.Returning):
        return list(returning.expressions or [])

    return []
