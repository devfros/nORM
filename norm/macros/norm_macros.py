from __future__ import annotations

from abc import ABC
from typing import Self, cast

from sqlglot import exp

from norm.errors import NormError, NormErrorCode

from .consts import INVALID_USE_ERROR_MSG
from .enums import NormMacrosEnum
from .signatures import MacroParamSignature, MacroSignature


def _is_norm_macro(node: exp.Expr, macro: NormMacrosEnum | None = None) -> bool:
    conditions = [
        isinstance(node, exp.Dot),
        isinstance(node.this, exp.Identifier) and node.this.output_name == "n",
        isinstance(node.expression, exp.Anonymous),
        node.name in NormMacrosEnum.member_values(),
    ]

    if macro:
        conditions.append(node.name == macro.value)

    return all(conditions)


class NormMacro(ABC):
    _signature: MacroSignature
    _param_names: list[str]
    expr: exp.Expr

    @property
    def macro_name(self) -> NormMacrosEnum:
        return self._signature.name

    @classmethod
    def extract_all_from(cls, expr: exp.Expr) -> list[Self]:
        macros = [
            item
            for item in expr.find_all(exp.Dot) or []
            if _is_norm_macro(item, cls._signature.name)
        ]
        return [cls(item) for item in macros]

    @classmethod
    def extract_from(cls, expr: exp.Expr) -> Self | None:
        if not _is_norm_macro(expr, cls._signature.name):
            return None

        return cls(cast("exp.Dot", expr))

    def __init__(self, expr: exp.Dot):
        if not self._signature.validate(expr):
            raise NormError(
                code=NormErrorCode.INVALID_MACRO_USAGE,
                message=INVALID_USE_ERROR_MSG.format(expr),
                hint=f"Usage: {self._signature.usage_hint()}",
                context={"macro": str(expr)},
            )
        self._param_names = [item.name for item in expr.expression.expressions]
        self.expr = expr

    def get_param(self, number: int) -> str | None:
        if len(self._param_names) < number:
            return None

        param = self._param_names[number - 1]
        return param if param != "_" else None


class ListMacro(NormMacro):
    _signature = MacroSignature(
        name=NormMacrosEnum.LIST,
        params=[
            MacroParamSignature(instanceof=exp.Placeholder),
        ],
    )

    name: str

    def __init__(self, exp: exp.Dot):
        super().__init__(exp)

        self.name = self.get_param(1)  # pyright: ignore[reportAttributeAccessIssue]


class NargMacro(ListMacro):
    _signature = MacroSignature(
        name=NormMacrosEnum.NARG,
        params=[
            MacroParamSignature(instanceof=exp.Placeholder),
        ],
    )


class EmbedMacro(ListMacro):
    _signature = MacroSignature(
        name=NormMacrosEnum.EMBED,
        params=[
            MacroParamSignature(name="table_name_or_alias", instanceof=exp.Column),
        ],
    )


class NembedMacro(EmbedMacro):
    _signature = MacroSignature(
        name=NormMacrosEnum.NEMBED,
        params=[
            MacroParamSignature(name="table_name_or_alias", instanceof=exp.Column),
        ],
    )


class OrdMacro(NormMacro):
    _signature = MacroSignature(
        name=NormMacrosEnum.ORD,
        params=[
            MacroParamSignature(
                name="table_name_or_alias", instanceof=exp.Column, optional=True
            ),
            MacroParamSignature(
                name="order_by", instanceof=exp.Placeholder, optional=True
            ),
            MacroParamSignature(name="desc", instanceof=exp.Placeholder, optional=True),
        ],
    )

    table: str | None
    order_by: str | None
    desc: str | None

    def __init__(self, exp: exp.Dot):
        super().__init__(exp)

        self.table = self.get_param(1)
        self.order_by = self.get_param(2)
        self.desc = self.get_param(3)
