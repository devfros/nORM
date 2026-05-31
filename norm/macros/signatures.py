from dataclasses import dataclass, field

from sqlglot import exp

from norm.macros import NormMacrosEnum


@dataclass
class MacroParamSignature:
    instanceof: type[exp.Column | exp.Placeholder]
    name: str = "name"
    optional: bool = field(default=False)

    def usage(self) -> str:
        prefix = ":" if self.instanceof == exp.Placeholder else ""
        optional = "?" if self.optional else ""
        return f"{prefix}{self.name}{optional}"


@dataclass
class MacroSignature:
    name: NormMacrosEnum
    params: list[MacroParamSignature] = field(default_factory=list)

    @property
    def min_params(self) -> int:
        return len([p for p in self.params if not p.optional])

    @property
    def max_params(self) -> int:
        return len(self.params)

    def validate(self, macro: exp.Dot) -> bool:
        if macro.name != self.name.value:
            return False

        expressions = macro.expression.expressions

        if self.max_params < len(expressions) or len(expressions) < self.min_params:
            return False

        if len(expressions) > 0:
            for ind, item in enumerate(expressions):
                param = self.params[ind]
                if not isinstance(item, param.instanceof):
                    return False

        return True

    def usage_hint(self) -> str:
        params_usage = ", ".join([p.usage() for p in self.params])
        return f"n.{self.name}({params_usage})"
