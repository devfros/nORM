import pytest

from .golden_cases import case_dir_for_name
from .runtime import discover_runtime_case_names, run_runtime_case

_RUNTIME_CASES = discover_runtime_case_names()


@pytest.mark.runtime
@pytest.mark.parametrize("case_name", _RUNTIME_CASES)
def test_python_runtime(case_name: str):
    run_runtime_case(case_dir_for_name(case_name), case_name=case_name)
