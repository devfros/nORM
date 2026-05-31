from abc import ABC, abstractmethod
from typing import TypeVar

from sqlglot import Dialects

from norm.schemas import GenOutputFiles
from norm.schemas.config import GenConfig
from norm.schemas.parsing import DBSchema
from norm.schemas.repo import Repo

from .dialect_profile import DialectProfile

DialectProfileType = TypeVar("DialectProfileType", bound=DialectProfile)


class BaseGenerator(ABC):
    dialect_profile: DialectProfileType

    def __init__(self, config: GenConfig, dialect: Dialects):
        self.config = config
        self.dialect = dialect

    @abstractmethod
    def generate(self, db_schema: DBSchema, repos: list[Repo]) -> GenOutputFiles:
        pass
