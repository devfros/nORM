from norm.gen.python.drivers.base import DriverProfile
from norm.gen.python.schemas import ImportData

AsyncmyProfile = DriverProfile(
    imports=ImportData(
        {
            "asyncmy": ["Connection"],
        }
    ),
    param_template="%s",
)

MySQLdbProfile = DriverProfile(
    imports=ImportData(
        {
            "MySQLdb": ["Connection"],
        }
    ),
    param_template="%s",
)
