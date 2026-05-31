from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenOutputFiles:
    _files: dict[Path, str] = field(default_factory=dict)  # path -> content

    def add_file(self, path: Path, content: str):
        self._files[Path(path)] = content

    def iter_files(self):
        return self._files.items()

    def create(self, out_path: Path):
        for file_path, content in self.iter_files():
            path = Path(out_path, file_path)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            with path.open(mode="w") as file:
                file.write(content)
