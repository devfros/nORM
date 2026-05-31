from sqlglot import Dialects

from norm.schemas.config import TargetConfig

from .base_generator import BaseGenerator
from .python.generator import PythonGenerator


def get_generator(config: TargetConfig) -> BaseGenerator | None:
    if config.gen.python:
        return PythonGenerator(config.gen, Dialects(config.sql.engine))
    # elif config.golang:
    #     return GolangGenerator
    # elif config.typescript:
    #     return TypeScriptGenerator

    return None
