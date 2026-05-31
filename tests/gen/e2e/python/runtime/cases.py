from pathlib import Path

from ..golden_cases import case_dir_for_name, discover_e2e_case_names

_RUNTIME_TEST_FILE = "runtime_test.py"


def runtime_test_path(case_dir: Path) -> Path:
    return case_dir / "runtime" / _RUNTIME_TEST_FILE


def discover_runtime_case_names() -> list[str]:
    names: list[str] = []
    for case_name in discover_e2e_case_names():
        case_dir = case_dir_for_name(case_name)
        if runtime_test_path(case_dir).is_file():
            names.append(case_name)
    return names
