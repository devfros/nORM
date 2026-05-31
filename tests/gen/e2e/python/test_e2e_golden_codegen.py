from pathlib import Path

import pytest

from .golden_cases import case_dir_for_name, case_out_dir, discover_e2e_case_names
from .pipeline import generate_case

_CASES = discover_e2e_case_names()


def _is_golden_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix == ".pyc":
        return False
    return "__pycache__" not in path.parts


@pytest.mark.parametrize("case_name", _CASES)
def test_python_codegen_matches_golden(case_name: str):
    case_dir = case_dir_for_name(case_name)
    generated = generate_case(case_dir)
    expected_dir = case_out_dir(case_dir)

    expected_paths = sorted(expected_dir.rglob("*"))
    expected_files = [path for path in expected_paths if _is_golden_file(path)]

    assert expected_files, f"Case '{case_name}' has no expected files."


    for expected_path in expected_files:
        rel_path = expected_path.relative_to(expected_dir)
        assert rel_path in generated, (
            f"Case '{case_name}' is missing generated file '{rel_path.as_posix()}'."
        )
        assert generated[rel_path] == expected_path.read_text(encoding="utf-8"), (
            f"Case '{case_name}' output mismatch for '{rel_path.as_posix()}'."
        )

    # expected_rel_paths = {path.relative_to(expected_dir) for path in expected_files}
    # extra_files = set(generated) - expected_rel_paths
    # assert not extra_files, (
    #     f"Case '{case_name}' generated unexpected files: "
    #     f"{sorted(path.as_posix() for path in extra_files)}"
    # )
