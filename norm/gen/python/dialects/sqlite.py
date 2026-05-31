from norm.gen.python.drivers.base import DriverProfile
from norm.gen.python.schemas import ImportData

AiosqliteProfile = DriverProfile(
    imports=ImportData(
        {
            "aiosqlite": ["Connection"],
        }
    ),
    param_template="?",
)

Sqlite3Profile = DriverProfile(
    imports=ImportData(
        {
            "contextlib": ["closing"],
            "sqlite3": ["Connection"],
        }
    ),
    param_template="?",
    close_sync_cursor=True,
)
