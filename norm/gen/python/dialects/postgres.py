from norm.gen.python.drivers.base import DriverProfile
from norm.gen.python.schemas import ImportData
from norm.schemas.repo import QueryCommandEnum

PsycopgAsyncProfile = DriverProfile(
    imports=ImportData(
        {
            "psycopg": ["AsyncConnection as Connection"],
        }
    ),
    param_template="%({})s",
    named_params=True,
    unsupported_query_commands={
        QueryCommandEnum.EXECLASTID,
    },
)

PsycopgSyncProfile = DriverProfile(
    imports=ImportData(
        {
            "psycopg": ["Connection"],
        }
    ),
    param_template="%({})s",
    named_params=True,
    unsupported_query_commands={
        QueryCommandEnum.EXECLASTID,
    },
)
