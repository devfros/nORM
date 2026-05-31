import pytest

from .runtime import ensure_runtime_env


def pytest_configure(config: pytest.Config) -> None:
    ensure_runtime_env()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "test_python_runtime" not in item.name:
            continue
        case_name = item.callspec.params["case_name"]
        engine = case_name.rsplit("/", 1)[-1]
        item.add_marker(getattr(pytest.mark, engine))
        if case_name.startswith("crud_async/"):
            item.add_marker(pytest.mark.async_mode)
