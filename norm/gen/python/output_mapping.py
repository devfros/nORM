from __future__ import annotations

from typing import TYPE_CHECKING

from norm.utils.identifier import normalize_identifier

from .schemas import OutputIndexMap

if TYPE_CHECKING:
    from collections.abc import Callable

    from norm.schemas.parsing import ModelDefinition

    from .schemas import ImportData


def build_output_map(
    model: ModelDefinition,
    schema_name: Callable[[ModelDefinition], str],
    *,
    start_index: int = 0,
    nullable: bool = False,
) -> OutputIndexMap:
    output_map: dict[int | str, str | OutputIndexMap] = {}
    index = start_index
    for name, field in model.fields.items():
        if field.model_datatype is not None:
            output_map[normalize_identifier(name)] = build_output_map(
                field.model_datatype,
                schema_name,
                start_index=index,
                nullable=field.constraints.nullable,
            )
            index += len(field.model_datatype.fields)
            continue

        output_map[index] = normalize_identifier(name)
        index += 1

    return OutputIndexMap(schema=schema_name(model), nullable=nullable, map=output_map)


def import_output_map_schemas(
    output_map: OutputIndexMap,
    imports: ImportData,
    *,
    db_model_names: frozenset[str],
    models_file_name: str,
) -> None:
    if output_map.schema not in db_model_names:
        return

    module = f".{models_file_name}"
    imports.add_import(module, [output_map.schema])
    for item in output_map.map.values():
        if isinstance(item, OutputIndexMap):
            import_output_map_schemas(
                item,
                imports,
                db_model_names=db_model_names,
                models_file_name=models_file_name,
            )
