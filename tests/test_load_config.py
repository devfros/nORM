from pathlib import Path

import pytest

from norm.config import load_norm_config
from norm.errors import NormError, NormErrorCode


def write_config(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_norm_config_accepts_valid_yaml(tmp_path: Path):
    config_path = tmp_path / "norm.yaml"
    write_config(
        config_path,
        """
version: "1"
targets:
  - name: api
    sql:
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories
      engine: postgres
    gen:
      out: ./norm_out
      python:
        asynchronous: true
        models: pydantic
        max_params: 1
""".strip(),
    )

    config = load_norm_config(config_path)

    assert config.version == "1"
    assert len(config.targets) == 1
    name = "api"
    assert config.targets.get(name) != None
    assert config.targets[name].sql.engine == "postgres"
    assert config.targets[name].gen.python is not None
    assert config.targets[name].gen.python.asynchronous is True


def test_load_norm_config_validation_error_uses_yaml_message(tmp_path: Path):
    config_path = tmp_path / "norm.yaml"
    write_config(
        config_path,
        """
version: "1"
targets:
  - name: api
    sql:
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories
      engine: mongodb
    gen:
      out: ./norm_out
""".strip(),
    )

    with pytest.raises(NormError) as err:
        load_norm_config(config_path)

    assert err.value.code == NormErrorCode.INVALID_CONFIG
    assert err.value.message == "Invalid norm.yaml configuration."
    assert "targets -> api -> sql -> engine" in str(err.value.context["details"])
    assert str(err.value.context["path"]) == str(config_path)


def test_load_norm_config_yaml_parse_error_is_wrapped(tmp_path: Path):
    config_path = tmp_path / "norm.yaml"
    write_config(
        config_path,
        """
version: "1"
targets:
  - name: api
    sql:
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories
      engine: postgres
    gen:
      out: ./norm_out
      python:
        asynchronous: true
        models: pydantic
        max_params: [1
""".strip(),
    )

    with pytest.raises(NormError) as err:
        load_norm_config(config_path)

    assert err.value.code == NormErrorCode.INVALID_CONFIG
    assert err.value.message == "Invalid norm.yaml configuration."
    assert "norm.yaml" in str(err.value.context["path"])


def test_load_norm_config_requires_targets(tmp_path: Path):
    config_path = tmp_path / "norm.yaml"
    write_config(config_path, 'version: "1"')

    with pytest.raises(NormError) as err:
        load_norm_config(config_path)

    assert err.value.code == NormErrorCode.INVALID_CONFIG
    assert "targets" in str(err.value.context["details"])
    assert "Field required" in str(err.value.context["details"])


def test_load_norm_config_rejects_duplicate_target_names(tmp_path: Path):
    config_path = tmp_path / "norm.yaml"
    write_config(
        config_path,
        """
version: "1"
targets:
  - name: api
    sql:
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories
      engine: postgres
    gen:
      out: ./norm_out/one
      python:
        asynchronous: true
  - name: api
    sql:
      db_schema: ./norm_in/schema.sql
      repositories: ./norm_in/repositories
      engine: postgres
    gen:
      out: ./norm_out/two
      python:
        asynchronous: false
""".strip(),
    )

    with pytest.raises(NormError) as err:
        load_norm_config(config_path)

    assert err.value.code == NormErrorCode.INVALID_CONFIG
    assert "duplicate names" in str(err.value.context["details"])
