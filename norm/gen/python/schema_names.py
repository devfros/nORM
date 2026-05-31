from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from norm.schemas.parsing import ModelKind
from norm.utils.identifier import normalize_identifier
from norm.utils.switch_case import snake_to_pascal

if TYPE_CHECKING:
    from collections.abc import Iterable

    from norm.schemas.parsing import DBSchema, EnumDefinition, ModelDefinition


class SchemaObjectNames:
    def __init__(
        self,
        db_schema: DBSchema,
        *,
        ambiguous_composite_names: frozenset[str],
        ambiguous_enum_names: frozenset[str],
    ) -> None:
        self._default_catalog = db_schema.default_catalog
        self._ambiguous_composite_names = ambiguous_composite_names
        self._ambiguous_enum_names = ambiguous_enum_names

    @classmethod
    def from_db_schema(cls, db_schema: DBSchema) -> SchemaObjectNames:
        return cls(
            db_schema,
            ambiguous_composite_names=_ambiguous_object_names(
                catalog.composite_types.keys()
                for catalog in db_schema.catalogs.values()
            ),
            ambiguous_enum_names=_ambiguous_object_names(
                catalog.enums.keys() for catalog in db_schema.catalogs.values()
            ),
        )

    def class_name(self, model: ModelDefinition) -> str:
        base = _pascal_case(model.model_name)
        if (
            model.kind != ModelKind.COMPOSITE
            or model.name not in self._ambiguous_composite_names
        ):
            return base

        catalog = model.catalog_name or self._default_catalog
        if catalog == self._default_catalog:
            return base

        return f"{_pascal_case(catalog)}{base}"

    def enum_class_name(self, enum: EnumDefinition) -> str:
        base = _pascal_case(enum.name)
        if enum.name not in self._ambiguous_enum_names:
            return base

        catalog = enum.catalog_name or self._default_catalog
        if catalog == self._default_catalog:
            return base

        return f"{_pascal_case(catalog)}{base}"


def _ambiguous_object_names(
    names_by_catalog: Iterable[Iterable[str]],
) -> frozenset[str]:
    counts: dict[str, int] = defaultdict(int)
    for names in names_by_catalog:
        for name in names:
            counts[name] += 1
    return frozenset(name for name, count in counts.items() if count > 1)


def _pascal_case(name: str) -> str:
    normalized = normalize_identifier(name, fallback="model", lowercase=False).lstrip(
        "_"
    )
    if normalized.isupper():
        normalized = normalized.lower()
    class_name = snake_to_pascal(normalized)
    return class_name if class_name[0].isalpha() else f"_{class_name}"
