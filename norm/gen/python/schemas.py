from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources


@dataclass
class PythonType:
    name: str
    args: list[PythonType] | None = None
    module: str | None = None
    quoted: bool = False

    @property
    def compiled(self) -> str:
        result = f"'{self.name}'" if self.quoted else self.name
        if self.args:
            args = ", ".join([arg.compiled for arg in self.args])
            result += f"[{args}]"

        return result

    @property
    def imports(self) -> ImportData:
        result = ImportData()
        if self.module:
            result.add_import(self.module, [self.name])

        if self.args:
            for arg in self.args:
                result.merge(arg.imports)

        return result


def _relative_last_sort_key(item: tuple[str, list]) -> tuple[bool, str]:
    module, _ = item
    return (module.startswith("."), module)


@dataclass
class ImportData:
    imports: dict[str, list[str]] = field(default_factory=dict)

    def __init__(self, initial: dict[str, list[str]] | None = None) -> None:
        self.imports = {}
        if initial:
            for module, names in initial.items():
                self.add_import(module, names)

    def add_import(self, module: str, names: list[str]):
        if module not in self.imports:
            self.imports[module] = []

        module_imports = [*self.imports[module], *names]

        self.imports[module] = list(set(module_imports))

    def merge(self, import_data: ImportData):
        for module, names in import_data.imports.items():
            self.add_import(module, names)

    def sorted_imports(self):
        sorted_imports = sorted(self.imports.items(), key=_relative_last_sort_key)
        return dict(sorted_imports)


@dataclass
class Util:
    name: str
    file_name: str
    resource_path: str
    gen_module_name: str
    additional_import_names: list[str] | None = None

    @property
    def gen_file_name(self):
        return f"{self.file_name}.py"

    @property
    def gen_import_names(self) -> list[str]:
        return [self.name, *(self.additional_import_names or [])]

    @property
    def gen_import_module(self):
        return f".{self.gen_module_name}.{self.file_name}"

    def get_content(self) -> str:
        return (
            resources.files(self.resource_path)
            .joinpath(f"{self.file_name}.py")
            .read_text(encoding="utf-8")
        )


@dataclass
class OutputIndexMap:
    schema: str
    nullable: bool
    map: dict[int | str, str | OutputIndexMap]
