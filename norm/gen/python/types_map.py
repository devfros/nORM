from collections.abc import Callable

from sqlglot import Dialects, exp
from sqlglot.expressions import DataType

from norm.parsing.datatypes import INLINE_ENUM_DATATYPE_KIND, enumcolumn_kind_name

from .schemas import PythonType


def _type(
    name: str, module: str | None = None, args: list[PythonType] | None = None
) -> PythonType:
    return PythonType(name=name, module=module, args=args)


DEFAULT_FIELD_TYPE = _type("Any", "typing")


def _common_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case "SMALLINT" | "INTEGER" | "INT" | "BIGINT":
            return _type("int")
        case "REAL" | "FLOAT" | "DOUBLE PRECISION":
            return _type("float")
        case "DECIMAL" | "NUMERIC":
            return _type("Decimal", "decimal")
        case "VARCHAR" | "CHARACTER VARYING" | "CHAR" | "CHARACTER" | "TEXT":
            return _type("str")
        case "BOOLEAN" | "BOOL":
            return _type("bool")
        case "DATE":
            return _type("date", "datetime")
        case "TIME" | "TIME WITH TIME ZONE" | "TIMETZ":
            return _type("time", "datetime")
        case "TIMESTAMP":
            return _type("datetime", "datetime")
        case "JSON" | "JSONB":
            return _type("Any", "typing")
        case "JSONOBJECT":
            return _type("dict")
        case "JSONARRAY":
            return _type(name="list", args=[_type("Any", "typing")])
        case "ARRAY":
            return _type("list")
        case "ANY" | "UNKNOWN":
            return _type("Any", "typing")
        case "NULL":
            return _type("None")
        case "ENUMCOLUMN":
            return _type(
                "Literal",
                "typing",
                args=[
                    PythonType(name=str(expr.this), quoted=expr.is_string)
                    for expr in datatype.expressions
                ],
            )
        case _:
            return None


def _postgres_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case (
            "INT2"
            | "INT4"
            | "INT8"
            | "SMALLSERIAL"
            | "SERIAL2"
            | "SERIAL"
            | "SERIAL4"
            | "BIGSERIAL"
            | "SERIAL8"
            | "OID"
            | "cid"
            | "xid"
            | "tid"
        ):
            return _type("int")
        case "FLOAT4" | "FLOAT8":
            return _type("float")
        case "NAME":
            return _type("str")
        case "BYTEA":
            return _type("bytes")
        case "TIMESTAMP WITH TIME ZONE" | "TIMESTAMPTZ" | "TIMESTAMP WITHOUT TIME ZONE":
            return _type("datetime", "datetime")
        case "INTERVAL" | "citext" | "ltree" | "lquery" | "ltxtquery":
            # Could use datetime.timedelta but PostgreSQL interval is more complex.
            return _type("str")
        case "UUID":
            return _type("UUID", "uuid")
        case (
            "INET"
            | "CIDR"
            | "MACADDR"
            | "MACADDR8"
            | "TSVECTOR"
            | "TSQUERY"
            | "POINT"
            | "LINE"
            | "LSEG"
            | "BOX"
            | "PATH"
            | "POLYGON"
            | "CIRCLE"
            | "INT4RANGE"
            | "INT8RANGE"
            | "NUMRANGE"
            | "TSRANGE"
            | "TSTZRANGE"
            | "DATERANGE"
            | "BIT"
            | "BIT VARYING"
            | "VARBIT"
            | "varbit"
            | "XML"
            | "ENUM"
            | "REGPROC"
            | "REGPROCEDURE"
            | "REGOPER"
            | "REGOPERATOR"
            | "REGCLASS"
            | "REGTYPE"
            | "REGNAMESPACE"
            | "REGROLE"
            | "MONEY"
            | "CSTRING"
        ):
            return _type("str")
        case "ARRAY":
            return _type("list")
        case "COMPOSITE" | "RECORD":
            return _type("dict")
        case "VOID":
            return _type("None")
        case (
            "TRIGGER"
            | "EVENT_TRIGGER"
            | "LANGUAGE_HANDLER"
            | "FDW_HANDLER"
            | "INTERNAL"
            | "OPAQUE"
        ):
            return _type("Any", "typing")
        case _:
            return _common_sql_type(datatype)


def _sqlite_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case "NULL":
            return _type("None")
        case "TINYINT" | "MEDIUMINT" | "UNSIGNED BIG INT" | "INT2" | "INT8":
            return _type("int")
        case "DOUBLE":
            return _type("float")
        case "BLOB" | "VARBINARY":
            return _type("bytes")
        case "CLOB" | "NATIVE CHARACTER" | "VARYING CHARACTER" | "NCHAR" | "NVARCHAR":
            return _type("str")
        case "DATETIME":
            return _type("datetime", "datetime")
        case _:
            return _common_sql_type(datatype)


def _mysql_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case "TINYINT" | "MEDIUMINT":
            return _type("int")
        case "UTINYINT" | "USMALLINT" | "UMEDIUMINT" | "UINT" | "UBIGINT":
            return _type("int")
        case "DATETIME" | "TIMESTAMPTZ":
            return _type("datetime", "datetime")
        case "YEAR":
            return _type("int")
        case "BINARY" | "VARBINARY" | "BLOB" | "TINYBLOB" | "MEDIUMBLOB" | "LONGBLOB":
            return _type("bytes")
        case "TINYTEXT" | "MEDIUMTEXT" | "LONGTEXT" | "ENUM" | "SET":
            return _type("str")
        case "BIT":
            return _type("int")
        case _:
            return _common_sql_type(datatype)


def _clickhouse_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case (
            "INT8"
            | "INT16"
            | "INT32"
            | "INT64"
            | "INT128"
            | "INT256"
            | "UINT8"
            | "UINT16"
            | "UINT32"
            | "UINT64"
            | "UINT128"
            | "UINT256"
            | "ENUM8"
            | "ENUM16"
        ):
            return _type("int")
        case "FLOAT32" | "FLOAT64":
            return _type("float")
        case "STRING" | "FIXEDSTRING" | "IPV4" | "IPV6":
            return _type("str")
        case "DATE32":
            return _type("date", "datetime")
        case "DATETIME" | "DATETIME64":
            return _type("datetime", "datetime")
        case "UUID":
            return _type("UUID", "uuid")
        case "ARRAY":
            return _type("list")
        case "MAP" | "JSON" | "OBJECT":
            return _type("dict")
        case "TUPLE" | "NESTED":
            return _type("tuple")
        case "NOTHING":
            return _type("None")
        case _:
            return _common_sql_type(datatype)


def _duckdb_sql_type(datatype: DataType) -> PythonType | None:
    datatype_key = _datatype_key(datatype)
    match datatype_key:
        case (
            "TINYINT"
            | "HUGEINT"
            | "UTINYINT"
            | "USMALLINT"
            | "UINTEGER"
            | "UBIGINT"
            | "UHUGEINT"
        ):
            return _type("int")
        case "DOUBLE":
            return _type("float")
        case "BLOB" | "BIT":
            return _type("bytes")
        case "TIMESTAMP WITH TIME ZONE" | "TIMESTAMPTZ":
            return _type("datetime", "datetime")
        case "UUID":
            return _type("UUID", "uuid")
        case "ARRAY" | "LIST":
            return _type("list")
        case "STRUCT" | "MAP" | "JSON":
            return _type("dict")
        case "UNION" | "ENUM" | "INTERVAL":
            return _type("str")
        case _:
            return _common_sql_type(datatype)


DialectTypeResolver = Callable[[DataType], PythonType | None]


def _datatype_key(datatype: DataType) -> str:
    if datatype.this == exp.DType.USERDEFINED:
        enumcolumn_kind = enumcolumn_kind_name(datatype.args.get("kind"))
        if enumcolumn_kind == INLINE_ENUM_DATATYPE_KIND:
            return enumcolumn_kind

        kind = datatype.args.get("kind")
        if isinstance(kind, exp.Identifier):
            return kind.name.strip().upper()

        for expression in datatype.expressions or []:
            if isinstance(expression, exp.DataType) and expression.this:
                return expression.this.name.strip().upper()

    return datatype.this.name.strip().upper()


def _resolve_python_type(
    datatype: DataType | None,
    dialect: Dialects,
    type_resolver: DialectTypeResolver,
) -> PythonType:
    if datatype is None:
        return DEFAULT_FIELD_TYPE

    resolved_type = type_resolver(datatype)

    if not resolved_type:
        return DEFAULT_FIELD_TYPE

    nested_datatypes = [
        expression
        for expression in datatype.expressions or []
        if isinstance(expression, exp.DataType)
    ]
    if nested_datatypes:
        resolved_type.args = []
        for nested in nested_datatypes:
            arg_type = get_python_type(nested, dialect)
            if arg_type:
                resolved_type.args.append(arg_type)

    return resolved_type


def get_postgres_python_type(datatype: DataType | None) -> PythonType:
    return _resolve_python_type(datatype, Dialects.POSTGRES, _postgres_sql_type)


def get_sqlite_python_type(datatype: DataType | None) -> PythonType:
    return _resolve_python_type(datatype, Dialects.SQLITE, _sqlite_sql_type)


def get_mysql_python_type(datatype: DataType | None) -> PythonType:
    return _resolve_python_type(datatype, Dialects.MYSQL, _mysql_sql_type)


def get_clickhouse_python_type(datatype: DataType | None) -> PythonType:
    return _resolve_python_type(datatype, Dialects.CLICKHOUSE, _clickhouse_sql_type)


def get_duckdb_python_type(datatype: DataType | None) -> PythonType:
    return _resolve_python_type(datatype, Dialects.DUCKDB, _duckdb_sql_type)


_TYPE_RESOLVERS = {
    Dialects.POSTGRES: get_postgres_python_type,
    Dialects.SQLITE: get_sqlite_python_type,
    Dialects.MYSQL: get_mysql_python_type,
    Dialects.CLICKHOUSE: get_clickhouse_python_type,
    Dialects.DUCKDB: get_duckdb_python_type,
}


def get_python_type(
    datatype: DataType | None,
    dialect: Dialects,
) -> PythonType:
    type_resolver = _TYPE_RESOLVERS.get(dialect, get_postgres_python_type)
    return type_resolver(datatype)
