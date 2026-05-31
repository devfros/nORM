from norm.schemas.repo import Repo

from .consts import Utils
from .schemas import ImportData, Util


def get_required_utils(repo: Repo) -> list[Util]:
    utils: list[Util] = []
    seen: set[str] = set()

    for repo_query in repo.processed_queries:
        if any(item.constraints.optional for item in repo_query.parameters.values()):
            if Utils.sentinel.name not in seen:
                seen.add(Utils.sentinel.name)
                utils.append(Utils.sentinel)

        if repo_query.filters and Utils.dynamic_filter.name not in seen:
            seen.add(Utils.dynamic_filter.name)
            utils.append(Utils.dynamic_filter)

    return utils


def get_utils_imports(repo: Repo) -> ImportData:
    imports = ImportData()
    for util in get_required_utils(repo):
        imports.add_import(util.gen_import_module, util.gen_import_names)
    return imports
