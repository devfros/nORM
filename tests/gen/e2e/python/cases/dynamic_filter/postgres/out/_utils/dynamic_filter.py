from .sentinel import UNSET


def _build(filter_tree: dict | None, params: dict) -> str | None:
    if not filter_tree:
        return None

    requred_params = filter_tree.get("p")
    grouped = filter_tree.get("g", False)
    node_value = filter_tree.get("v")

    if node_value:
        node_value = f"({node_value})" if grouped else node_value

        if not requred_params:
            return node_value

        if all(params.get(param, UNSET) is not UNSET for param in requred_params):
            return node_value

        return None

    node = filter_tree.get("t")
    left_node = filter_tree.get("l")
    right_node = filter_tree.get("r")

    left = _build(left_node, params)
    right = _build(right_node, params)
    result = None

    if left and right:
        result = f"{left} {node} {right}"
    elif left:
        result = left
    elif not left_node and right:
        result = f"{node} {right}"
    elif right:
        result = right

    if not result:
        return None

    return result if not grouped else f"({result})"


def build_filter_clauses(query: str, params: dict, clauses: dict) -> str:
    for key, filter_item in clauses.items():
        clause_name = filter_item.get("clause")
        clause = filter_item.get("tree")
        filter_clause = _build(clause, params)
        query = query.replace(
            key, f"{clause_name} {filter_clause}" if filter_clause else ""
        )

    return query
