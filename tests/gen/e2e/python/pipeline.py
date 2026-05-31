from pathlib import Path

from norm.cli.gen import generate_target
from norm.config import load_norm_config


def generate_case(case_dir: Path) -> dict[Path, str]:
    case_dir = case_dir.resolve()
    config = load_norm_config(case_dir / "norm.yaml")

    if not config.targets:
        raise AssertionError(f"Case '{case_dir.name}' has no targets in norm.yaml.")

    target = next(iter(config.targets.values()))
    if target.gen.python is None:
        raise AssertionError(f"Case '{case_dir.name}' has no python gen config.")

    output, _stats = generate_target(target, base_dir=case_dir)
    return dict(output.iter_files())
