from __future__ import annotations

from pathlib import Path

from .case_loader import dialect_dir

_CASES_ROOT = Path(__file__).resolve().parent / "cases"
_SUITES = ("parameters", "return_fields", "dynamic_filtering")


def cases_root() -> Path:
    return _CASES_ROOT


def case_dir_for_id(case_id: str) -> Path:
    suite, case_name, _dialect = case_id.split("/", 2)
    return _CASES_ROOT / suite / case_name


def discover_processing_case_ids() -> list[str]:
    if not _CASES_ROOT.is_dir():
        return []

    case_ids: list[str] = []
    for suite in _SUITES:
        suite_dir = _CASES_ROOT / suite
        if not suite_dir.is_dir():
            continue

        for case_dir in sorted(suite_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            for dialect_dir_path in sorted(case_dir.iterdir()):
                if not dialect_dir_path.is_dir():
                    continue

                dialect = dialect_dir_path.name
                if not (dialect_dir(case_dir, dialect) / "input.sql").is_file():
                    continue
                if not (dialect_dir(case_dir, dialect) / "output.json").is_file():
                    continue

                case_ids.append(f"{suite}/{case_dir.name}/{dialect}")

    return case_ids
