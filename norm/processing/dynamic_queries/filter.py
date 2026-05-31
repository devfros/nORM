from collections.abc import Callable

from sqlglot import Dialects, Expr, exp

from norm.consts import MetaKeys
from norm.schemas.dynamic_filter import DynamicFilter, FilterTree

PostprocessCallback = Callable[[Expr], Expr]


def get_filter_clauses(query: exp.Expr) -> list[exp.Where | exp.Having]:
    """
    Returns top-level WHERE and HAVING clauses
    """
    result = []
    exp_types = [exp.Where, exp.Having]

    for expr in exp_types:
        for found in query.find_all(expr, bfs=True):
            if (
                found.find_ancestor(exp.Where) is not None
                or found.find_ancestor(exp.Having) is not None
            ):
                continue
            result.append(found)

    return result


def process_filter_clause(
    filter_clause: exp.Where | exp.Having,
    dialect: Dialects,
    enforce: bool,
    postprocess: PostprocessCallback | None = None,
) -> DynamicFilter | None:
    """
    Build filter tree for WHERE/HAVING clauses
    """
    if isinstance(filter_clause, exp.Having):
        clause = "HAVING"
    else:
        clause = "WHERE"

    optionals = [
        p
        for p in list(filter_clause.find_all(exp.Placeholder))
        if p.meta.get(MetaKeys.OPTIONAL, False)
    ]

    if not enforce and len(optionals) == 0:
        return None

    tree = _clause_dfs(filter_clause.this, dialect, postprocess)

    if not tree:
        return None

    return DynamicFilter(clause=clause, tree=tree)


def _clause_dfs(
    node: Expr,
    dialect: Dialects,
    pc: PostprocessCallback | None = None,
) -> FilterTree | None:
    has_paren = None

    if isinstance(node, exp.Paren):
        node = node.this
        has_paren = True

    if isinstance(node, (exp.Or, exp.And)):
        return FilterTree(
            t=node.sql_name(),
            g=has_paren,
            l=_clause_dfs(node.left, dialect, pc),
            r=_clause_dfs(node.right, dialect, pc),
        )

    if isinstance(node, (exp.Not)):
        return FilterTree(
            t=node.key.upper(),
            g=has_paren,
            r=_clause_dfs(node.this, dialect, pc),
        )

    optionals = [
        ph.name
        for ph in node.find_all(exp.Placeholder)
        if ph.meta.get(MetaKeys.OPTIONAL, False)
    ]

    if pc:
        node = pc(node)

    return FilterTree(
        g=has_paren,
        p=optionals or None,
        v=node.sql(pretty=True, comments=True, max_text_width=50, dialect=dialect),
    )
