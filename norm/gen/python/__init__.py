from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "ImportData",
    "PythonGenerator",
    "PythonType",
    "get_required_utils",
    "get_utils_imports",
]


def __getattr__(name: str) -> Any:
    if name in {"ImportData", "PythonType"}:
        module = import_module(".schemas", __name__)
    elif name == "PythonGenerator":
        module = import_module(".generator", __name__)
    elif name == "generate_repo":
        module = import_module(".repos", __name__)
    elif name in {"get_required_utils", "get_utils_imports"}:
        module = import_module(".utils_funcs", __name__)
    else:
        msg = f"module '{__name__}' has no attribute '{name}'"
        raise AttributeError(msg)

    return getattr(module, name)
