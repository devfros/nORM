from __future__ import annotations

import copy
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class CoreSchema:
    def to_dict(self, exclude_none: bool = False) -> dict:
        data: dict = {}
        for field_item in fields(self):
            if field_item.metadata.get("exclude", False):
                continue
            value = getattr(self, field_item.name)
            serialized = _serialize(value, exclude_none=exclude_none)
            if exclude_none and serialized is None:
                continue
            data[field_item.name] = serialized
        return data

    def model_dump(self, exclude_none: bool = False) -> dict:
        return self.to_dict(exclude_none=exclude_none)

    def model_copy(self, deep: bool = False):
        if deep:
            return copy.deepcopy(self)
        return copy.copy(self)


def _serialize(value: Any, exclude_none: bool) -> Any:
    if value is None:
        return None

    if isinstance(value, CoreSchema):
        return value.model_dump(exclude_none=exclude_none)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, range):
        return [value.start, value.stop]

    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            serialized = _serialize(item, exclude_none=exclude_none)
            if exclude_none and serialized is None:
                continue
            result[key] = serialized
        return result

    if isinstance(value, list):
        result = []
        for item in value:
            serialized = _serialize(item, exclude_none=exclude_none)
            if exclude_none and serialized is None:
                continue
            result.append(serialized)
        return result

    if is_dataclass(value):
        data = {}
        for field_item in fields(value):
            if field_item.metadata.get("exclude", False):
                continue
            item = getattr(value, field_item.name)
            serialized = _serialize(item, exclude_none=exclude_none)
            if exclude_none and serialized is None:
                continue
            data[field_item.name] = serialized
        return data

    return value
