from __future__ import annotations

from typing import NoReturn

from norm.errors import NormError, NormErrorCode


def raise_norm_optimize_error(err: Exception, query: object) -> NoReturn:
    message = str(err)
    if "unknown table" in message.lower():
        raise NormError(
            code=NormErrorCode.UNKNOWN_TABLE,
            message=message,
            context={"query": str(query)},
        ) from err

    raise NormError(
        code=NormErrorCode.OPTIMIZATION_ERROR,
        message=message,
        context={"query": str(query)},
    ) from err
