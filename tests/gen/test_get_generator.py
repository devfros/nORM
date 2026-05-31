from sqlglot import Dialects

from norm.gen.get_generator import get_generator
from norm.gen.python.generator import PythonGenerator
from norm.schemas.config import GenConfig, PythonGenConfig, SqlConfig, TargetConfig


def _target_config(*, python: PythonGenConfig | None, engine: str) -> TargetConfig:
    return TargetConfig(
        name="api",
        sql=SqlConfig(
            db_schema="./schema.sql",
            repositories="./repositories",
            engine=engine,
        ),
        gen=GenConfig(out="./generated", python=python),
    )


def test_get_generator_returns_python_generator_for_python_target():
    target = _target_config(
        python=PythonGenConfig(asynchronous=True, models="dataclasses", max_params=1),
        engine=Dialects.POSTGRES.value,
    )

    generator = get_generator(target)

    assert isinstance(generator, PythonGenerator)
    assert generator.dialect == Dialects.POSTGRES


def test_get_generator_returns_none_without_supported_generator_config():
    target = _target_config(python=None, engine=Dialects.POSTGRES.value)

    generator = get_generator(target)

    assert generator is None


def test_get_generator_uses_target_sql_engine_for_dialect():
    target = _target_config(
        python=PythonGenConfig(asynchronous=True, models="pydantic", max_params=2),
        engine=Dialects.MYSQL.value,
    )

    generator = get_generator(target)

    assert isinstance(generator, PythonGenerator)
    assert generator.dialect == Dialects.MYSQL
