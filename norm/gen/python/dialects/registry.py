from sqlglot import Dialects

from norm.gen.python.drivers.base import DriverProfile, PythonDialectProfile

from . import clickhouse, duckdb, mysql, postgres, sqlite

_DEFAULT = Dialects.POSTGRES

DIALECT_DRIVER_MAP: dict[Dialects, dict[bool, DriverProfile]] = {
    Dialects.CLICKHOUSE: {
        True: clickhouse.AsynchProfile,
        False: clickhouse.ClickhouseDriverProfile,
    },
    Dialects.DUCKDB: {
        True: duckdb.AioduckProfile,
        False: duckdb.DuckdbProfile,
    },
    Dialects.MYSQL: {
        True: mysql.AsyncmyProfile,
        False: mysql.MySQLdbProfile,
    },
    Dialects.SQLITE: {
        True: sqlite.AiosqliteProfile,
        False: sqlite.Sqlite3Profile,
    },
    Dialects.POSTGRES: {
        True: postgres.PsycopgAsyncProfile,
        False: postgres.PsycopgSyncProfile,
    },
}


def get_python_dialect_profile(
    dialect: Dialects, is_async: bool
) -> PythonDialectProfile:
    driver = DIALECT_DRIVER_MAP.get(dialect, {}).get(is_async, None)
    if not driver:
        driver = DIALECT_DRIVER_MAP[_DEFAULT][is_async]

    return PythonDialectProfile(
        dialect=dialect,
        param_template=driver.param_template,
        unsupported_query_commands=driver.unsupported_query_commands,
        driver=driver,
    )
