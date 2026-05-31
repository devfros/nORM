from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from norm.schemas.parsing import DBSchema
    from norm.schemas.repo import ProcessedQuery, Repo


@dataclass(frozen=True)
class RepoSpec:
    name: str
    file_name: str
    processed_queries: tuple[ProcessedQuery, ...]
    source: Repo

    @classmethod
    def from_repo(cls, repo: Repo) -> RepoSpec:
        return cls(
            name=repo.name,
            file_name=repo.file_name,
            processed_queries=tuple(repo.processed_queries),
            source=repo,
        )


@dataclass(frozen=True)
class GenerationSpec:
    db_schema: DBSchema
    repos: tuple[RepoSpec, ...]

    @classmethod
    def from_inputs(cls, db_schema: DBSchema, repos: list[Repo]) -> GenerationSpec:
        return cls(
            db_schema=db_schema,
            repos=tuple(RepoSpec.from_repo(repo) for repo in repos),
        )
