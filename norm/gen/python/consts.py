from dataclasses import dataclass

from .schemas import Util

MODELS_DIR_NAME = "models"
UTILS_DIR_NAME = "_utils"
REPOS_DIR_NAME = "repos"

UTILS_RESOURCE_PATH = "norm.gen.python.utils"
UNSET_SENTINEL = "UNSET"


@dataclass
class VarNames:
    arg = "arg"
    query = "query"
    params = "params"
    db = "db"
    db_cursor = "cur"
    result = "result"
    result_item = "item"


@dataclass
class Utils:
    sentinel = Util(
        name=UNSET_SENTINEL,
        file_name="sentinel",
        resource_path=UTILS_RESOURCE_PATH,
        gen_module_name=UTILS_DIR_NAME,
        additional_import_names=[],
    )
    dynamic_filter = Util(
        name="build_filter_clauses",
        file_name="dynamic_filter",
        resource_path=UTILS_RESOURCE_PATH,
        gen_module_name=UTILS_DIR_NAME,
        additional_import_names=[],
    )
