from __future__ import annotations

import re
from typing import TYPE_CHECKING

from norm.utils.identifier import normalize_identifier
from norm.utils.switch_case import snake_to_pascal

if TYPE_CHECKING:
    from norm.schemas.parsing import EnumDefinition, LiteralValue

_ENUM_IDENTIFIER_CHARS = re.compile(r"[^0-9A-Za-z_]+")
_ENUM_WORD_SEPARATORS = re.compile(r"[-:/]+")


def model_class_name(name: str) -> str:
    normalized = normalize_identifier(name, fallback="model", lowercase=False).lstrip(
        "_"
    )
    if normalized.isupper():
        normalized = normalized.lower()
    class_name = snake_to_pascal(normalized)
    return class_name if class_name[0].isalpha() else f"_{class_name}"


def enum_values(enum: EnumDefinition, class_name: str) -> list[dict[str, str]]:
    common_prefix = _common_enum_value_prefix(enum.values)
    use_class_prefix = common_prefix is None and any(
        _needs_enum_prefix(value) for value in enum.values
    )
    use_single_quotes = enum.quoted

    return [
        {
            "name": _enum_member_name(
                value=value,
                index=index,
                class_name=class_name,
                common_prefix=common_prefix,
                use_class_prefix=use_class_prefix,
            ),
            "literal": _python_string_literal(str(value.value), use_single_quotes),
        }
        for index, value in enumerate(enum.values)
    ]


def _enum_member_name(
    *,
    value: LiteralValue,
    index: int,
    class_name: str,
    common_prefix: str | None,
    use_class_prefix: bool,
) -> str:
    raw_value = str(value.value)
    normalized = _normalized_enum_value(raw_value)

    if not normalized:
        return f"{class_name.upper()}VALUE{index}"

    if normalized[0].isdigit():
        return f"{class_name.upper()}{normalized}"

    if common_prefix is not None:
        return f"{common_prefix.upper()}{normalized.replace('_', '').upper()}"

    if use_class_prefix:
        return f"{class_name}{snake_to_pascal(normalized.lower())}"

    return normalized.upper()


def _common_enum_value_prefix(values: list[LiteralValue]) -> str | None:
    normalized_values = [
        _normalized_enum_value(str(value.value)).lower() for value in values
    ]
    alpha_prefixes: list[str] = []
    for value in normalized_values:
        match = re.match(r"[a-z]+", value)
        if match:
            alpha_prefixes.append(match.group(0))
    if len(alpha_prefixes) != len(normalized_values):
        return None

    prefix = alpha_prefixes[0] if alpha_prefixes else ""
    if not prefix or not all(value.startswith(prefix) for value in normalized_values):
        return None

    # A shared prefix is useful only for values like foo-a/foo_b/foo:c. For plain
    # values (admin/user), uppercase constants are clearer and match existing output.
    if not any(_needs_enum_prefix(value) for value in values):
        return None

    return prefix


def _needs_enum_prefix(value: LiteralValue) -> bool:
    raw_value = str(value.value)
    return raw_value != _normalized_enum_value(raw_value)


def _normalized_enum_value(value: str) -> str:
    value = _ENUM_WORD_SEPARATORS.sub("_", value)
    return _ENUM_IDENTIFIER_CHARS.sub("", value).strip("_")


def _python_string_literal(value: str, use_single_quotes: bool) -> str:
    quote = "'" if use_single_quotes else '"'
    escaped = value.replace("\\", "\\\\").replace(quote, f"\\{quote}")
    return f"{quote}{escaped}{quote}"
