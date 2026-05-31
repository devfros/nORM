from norm.gen.base_generator import BaseGenerator
from norm.schemas import DBSchema, GenOutputFiles, Repo


class GolangGenerator(BaseGenerator):
    def generate(self, db_schema: DBSchema, repos: list[Repo]) -> GenOutputFiles:  # noqa: ARG002
        output = GenOutputFiles()
        # TODO: Implement
        return output
