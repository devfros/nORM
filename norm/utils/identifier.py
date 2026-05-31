import keyword
import re

_INVALID_IDENTIFIER_CHARS = re.compile(r"[^0-9A-Za-z]+")


def normalize_identifier(
    value: str,
    fallback: str = "value",
    *,
    lowercase: bool = True,
) -> str:
    name = _INVALID_IDENTIFIER_CHARS.sub("_", value).strip("_")

    if lowercase:
        name = name.lower()

    if not name:
        name = fallback

    if name[0].isdigit():
        name = f"_{name}"

    if keyword.iskeyword(name):
        name = f"{name}_"

    return name
