from __future__ import annotations

import pytest

from norm.utils.switch_plurality import switch_plurality


@pytest.mark.parametrize(
    ("plural", "singular"),
    [
        ("users", "user"),
        ("items", "item"),
        ("categories", "category"),
        ("addresses", "address"),
        ("boxes", "box"),
        ("order_items", "order_item"),
        ("people", "person"),
        ("children", "child"),
        ("men", "man"),
        ("women", "woman"),
        ("oxen", "ox"),
        ("leaves", "leaf"),
        ("wives", "wife"),
        ("lives", "life"),
        ("wolves", "wolf"),
        ("bacteria", "bacterium"),
        ("criteria", "criterion"),
        ("phenomena", "phenomenon"),
        ("indices", "index"),
        ("matrices", "matrix"),
        ("analyses", "analysis"),
        ("schemas", "schema"),
        ("schemata", "schema"),
        ("fungi", "fungus"),
        ("cacti", "cactus"),
        ("status", "status"),
        ("species", "species"),
        ("series", "series"),
    ],
)
def test_to_singular(plural: str, singular: str) -> None:
    assert switch_plurality(plural, to_singular=True) == singular


@pytest.mark.parametrize(
    ("singular", "plural"),
    [
        ("user", "users"),
        ("category", "categories"),
        ("address", "addresses"),
        ("box", "boxes"),
    ],
)
def test_to_plural(singular: str, plural: str) -> None:
    assert switch_plurality(singular, to_singular=False) == plural


def test_matrices_not_in_data_uses_rules() -> None:
    # matrix -> matrices via -ices pattern not in our stem list; -es rule
    assert switch_plurality("matrices", to_singular=True) == "matrix"
