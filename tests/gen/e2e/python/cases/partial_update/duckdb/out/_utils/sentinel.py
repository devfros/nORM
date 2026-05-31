from typing import Any, Final


class _UNSET(Any):
    def __repr__(self) -> str:
        return "UNSET"

    @classmethod
    def to_bool(cls, value: Any) -> bool:
        return not isinstance(value, cls)

    @classmethod
    def to_none(cls, value: Any) -> Any | None:
        return None if not cls.to_bool(value) else value


UNSET: Final = _UNSET()
