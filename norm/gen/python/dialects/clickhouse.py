from norm.gen.python.drivers.base import DriverProfile
from norm.gen.python.schemas import ImportData
from norm.schemas.repo import QueryCommandEnum

AsynchProfile = DriverProfile(
    imports=ImportData(
        {
            "asynch": ["Connection"],
        }
    ),
    param_template="%({})s",
    named_params=True,
    unsupported_query_commands={
        QueryCommandEnum.EXECLASTID,
    },
)

ClickhouseDriverProfile = DriverProfile(
    imports=ImportData(
        {
            "contextlib": ["closing"],
            "clickhouse_driver.dbapi.connection": ["Connection"],
        }
    ),
    param_template="%({})s",
    close_sync_cursor=True,
    named_params=True,
    unsupported_query_commands={
        QueryCommandEnum.EXECLASTID,
    },
)
