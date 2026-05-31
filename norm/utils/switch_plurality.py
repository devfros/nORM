from __future__ import annotations

import re

from norm.utils.plurality_data import PLURAL_TO_SINGULAR, SI_UNINFLECTED

_ES_SUFFIX = re.compile(r"(ches|shes|ses|xes|zes)$", re.IGNORECASE)
_MIN_PLURAL_LEN = 2
_MIN_IES_LEN = 3
_MIN_ICES_LEN = 4
_MIN_IVES_LEN = 4
_MIN_VES_LEN = 3
_MIN_OES_LEN = 3


def switch_plurality(value: str, to_singular: bool = True) -> str:
    if to_singular:
        return _to_singular(value)
    return _to_plural(value)


def _match_case(source: str, result: str) -> str:
    if source.isupper():
        return result.upper()
    if source[0].isupper():
        return result.capitalize()
    return result


def _lookup_plural(word: str) -> str | None:
    lower = word.lower()
    if lower in SI_UNINFLECTED:
        return word
    singular = PLURAL_TO_SINGULAR.get(lower)
    if singular is None:
        return None
    return _match_case(word, singular)


def _to_singular(name: str) -> str:
    if len(name) < _MIN_PLURAL_LEN:
        return name

    matched = _lookup_plural(name)
    if matched is not None:
        return matched

    lower = name.lower()

    if lower.endswith("ices") and len(name) > _MIN_ICES_LEN:
        return name[:-3] + ("IX" if name[-3].isupper() else "ix")

    if lower.endswith("ives") and len(name) > _MIN_IVES_LEN:
        return name[:-4] + ("FE" if name[-4].isupper() else "fe")

    if lower.endswith("ves") and len(name) > _MIN_VES_LEN:
        return name[:-3] + ("F" if name[-3].isupper() else "f")

    if lower.endswith("ies") and len(name) > _MIN_IES_LEN:
        suffix = "Y" if name[-3].isupper() else "y"
        return name[:-3] + suffix

    if lower.endswith("oes") and len(name) > _MIN_OES_LEN:
        return name[:-2]

    if _ES_SUFFIX.search(lower):
        return name[:-2]

    if lower.endswith("s") and not lower.endswith("ss"):
        return name[:-1]

    return name


def _to_plural(name: str) -> str:
    if len(name) < 1:
        return name

    lower = name.lower()

    for plural, singular in PLURAL_TO_SINGULAR.items():
        if lower == singular:
            return _match_case(name, plural)

    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return name + ("ES" if name[-1].isupper() else "es")

    if lower.endswith("y") and len(name) > 1 and name[-2] not in "aeiouAEIOU":
        return name[:-1] + ("IES" if name[-1].isupper() else "ies")

    if lower.endswith("s"):
        return name

    return name + ("S" if name[-1].isupper() else "s")
