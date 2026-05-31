from enum import StrEnum


class MetaKeys(StrEnum):
    TABLE_NAME = "norm_table_name"
    CATALOG_NAME = "norm_catalog_name"
    EMBED = "norm_embed"
    LIST_KEY = "norm_list_key"

    NULLABLE = "norm_nullable"
    OPTIONAL = "norm_optional"

    PARAM_KIND = "norm_param_kind"
