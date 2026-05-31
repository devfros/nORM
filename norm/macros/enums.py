from enum import StrEnum


class NormMacrosEnum(StrEnum):
    NARG = "narg"
    LIST = "list"
    ORD = "ord"
    EMBED = "embed"
    NEMBED = "nembed"

    @classmethod
    def member_values(cls) -> list[str]:
        return [item.value for item in cls._member_map_.values()]
