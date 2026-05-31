from pathlib import Path

from norm.config import load_norm_config

_CASES_ROOT = Path(__file__).resolve().parent / "cases"


def cases_root() -> Path:
    return _CASES_ROOT


def _case_has_inputs(case_dir: Path, target) -> bool:
    schema_path = (case_dir / target.sql.db_schema).resolve()
    repos_dir = (case_dir / target.sql.repositories).resolve()

    if not schema_path.is_file():
        return False

    if not repos_dir.is_dir():
        return False

    return any(repos_dir.glob("*.sql"))


def _is_valid_case_dir(case_dir: Path) -> bool:
    config_path = case_dir / "norm.yaml"
    if not config_path.is_file():
        return False

    in_dir = case_dir / "in"
    out_dir = case_dir / "out"
    if not in_dir.is_dir() or not out_dir.is_dir():
        return False

    config = load_norm_config(config_path)
    if not config.targets:
        return False

    target = next(iter(config.targets.values()))
    if target.gen.python is None:
        return False

    if not _case_has_inputs(case_dir, target):
        return False

    return True


def discover_e2e_case_names() -> list[str]:
    if not _CASES_ROOT.is_dir():
        return []

    names: list[str] = []
    for scenario_dir in sorted(_CASES_ROOT.iterdir()):
        if not scenario_dir.is_dir():
            continue

        for engine_dir in sorted(scenario_dir.iterdir()):
            if not engine_dir.is_dir():
                continue

            if not _is_valid_case_dir(engine_dir):
                continue

            names.append(f"{scenario_dir.name}/{engine_dir.name}")

    return names


def case_dir_for_name(case_name: str) -> Path:
    return cases_root() / case_name


def case_out_dir(case_dir: Path) -> Path:
    return case_dir / "out"
