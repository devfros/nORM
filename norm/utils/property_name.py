from collections.abc import Container


def unique_property_name(
    names: Container[str],
    name: str,
) -> str:
    if name not in names:
        return name

    suffix = 2
    while f"{name}_{suffix}" in names:
        suffix += 1
    return f"{name}_{suffix}"
