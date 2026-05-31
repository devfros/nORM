from norm.gen.python.drivers.base import DriverProfile
from norm.gen.python.schemas import ImportData
from norm.schemas.repo import QueryCommandEnum

AioduckProfile = DriverProfile(
    imports=ImportData(
        {
            "aioduck": ["AsyncConnection as Connection"],
        }
    ),
    param_template="?",
    unsupported_query_commands={
        QueryCommandEnum.EXECROWS,
        QueryCommandEnum.EXECLASTID,
    },
)

DuckdbProfile = DriverProfile(
    imports=ImportData(
        {
            "contextlib": ["closing"],
            "duckdb": ["DuckDBPyConnection as Connection"],
        }
    ),
    param_template="?",
    close_sync_cursor=True,
    unsupported_query_commands={
        QueryCommandEnum.EXECROWS,
        QueryCommandEnum.EXECLASTID,
    },
)
