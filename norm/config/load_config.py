from pathlib import Path

import yaml

from norm.errors import NormError, NormErrorCode
from norm.schemas import ConfigValidationError, NormConfig


def load_norm_config(path: str | Path) -> NormConfig:
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as err:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Invalid norm.yaml configuration.",
            hint="Fix YAML syntax errors and run the command again.",
            context={"details": str(err), "path": str(path)},
        ) from err

    if data is None:
        data = {}

    try:
        config = NormConfig.from_dict(data)
    except ConfigValidationError as err:
        lines = []
        for error in err.errors():
            loc = " -> ".join(str(part) for part in error["loc"]) or "(root)"
            lines.append(f"  {loc}: {error['msg']}")
        detail = "\n".join(lines)
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message="Invalid norm.yaml configuration.",
            context={"details": detail, "path": str(path)},
        ) from err

    return config
