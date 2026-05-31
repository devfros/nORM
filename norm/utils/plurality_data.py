from __future__ import annotations

_PL_SB_IRREGULAR: dict[str, str] = {
    "child": "children",
    "chili": "chilis|chilies",
    "brother": "brothers|brethren",
    "infinity": "infinities|infinity",
    "loaf": "loaves",
    "lore": "lores|lore",
    "hoof": "hoofs|hooves",
    "beef": "beefs|beeves",
    "thief": "thiefs|thieves",
    "money": "monies",
    "mongoose": "mongooses",
    "ox": "oxen",
    "cow": "cows|kine",
    "graffito": "graffiti",
    "octopus": "octopuses|octopodes",
    "genie": "genies|genii",
    "ganglion": "ganglions|ganglia",
    "trilby": "trilbys",
    "turf": "turfs|turves",
    "numen": "numina",
    "atman": "atmas",
    "occiput": "occiputs|occipita",
    "sabretooth": "sabretooths",
    "sabertooth": "sabertooths",
    "lowlife": "lowlifes",
    "flatfoot": "flatfoots",
    "tenderfoot": "tenderfoots",
    "romany": "romanies",
    "jerry": "jerries",
    "mary": "maries",
    "talouse": "talouses",
    "rom": "roma",
    "carmen": "carmina",
    "corpus": "corpuses|corpora",
    "opus": "opuses|opera",
    "genus": "genera",
    "mythos": "mythoi",
    "penis": "penises|penes",
    "testis": "testes",
    "atlas": "atlases|atlantes",
    "yes": "yeses",
}


def _build_si_sb_irregular() -> dict[str, str]:
    inverted: dict[str, str] = {}
    for singular, plural in _PL_SB_IRREGULAR.items():
        for plural_form in plural.split("|"):
            inverted[plural_form] = singular
    return inverted


_UM_A_SINGULARS = (
    "bacterium",
    "agendum",
    "desideratum",
    "erratum",
    "stratum",
    "datum",
    "ovum",
    "extremum",
    "candelabrum",
    "maximum",
    "minimum",
    "momentum",
    "optimum",
    "quantum",
    "cranium",
    "curriculum",
    "dictum",
    "phylum",
    "medium",
    "vacuum",
    "consortium",
)

_US_I_SINGULARS = (
    "alumnus",
    "alveolus",
    "bacillus",
    "bronchus",
    "locus",
    "nucleus",
    "stimulus",
    "meniscus",
    "sarcophagus",
    "focus",
    "radius",
    "genius",
    "fungus",
    "cactus",
    "hippopotamus",
)

_ON_A_SINGULARS = (
    "criterion",
    "phenomenon",
    "noumenon",
    "organon",
    "oxymoron",
)

_EX_IX_ICES_SINGULARS = (
    "codex",
    "murex",
    "vortex",
    "vertex",
    "cortex",
    "latex",
    "apex",
    "index",
    "simplex",
    "radix",
    "helix",
    "appendix",
    "matrix",
)

_IS_IDES_SINGULARS = (
    "ephemeris",
    "iris",
    "chrysalis",
)

_A_ATA_SINGULARS = (
    "schema",
    "stigma",
    "stoma",
    "dogma",
    "lemma",
    "enigma",
    "drama",
)

_EN_INA_SINGULARS = (
    "stamen",
    "foramen",
    "lumen",
)

_VES_VE_SINGULARS: dict[str, str] = {
    "interweave": "interweaves",
    "weave": "weaves",
    "olive": "olives",
    "bivalve": "bivalves",
    "dissolve": "dissolves",
    "resolve": "resolves",
    "salve": "salves",
    "twelve": "twelves",
    "valve": "valves",
    "wolf": "wolves",
    "wife": "wives",
    "knife": "knives",
    "life": "lives",
    "leaf": "leaves",
    "half": "halves",
    "self": "selves",
    "calf": "calves",
}

_ES_IS_SINGULARS = (
    "analysis",
    "axis",
    "basis",
    "crisis",
    "diagnosis",
    "hypothesis",
    "oasis",
    "parenthesis",
    "synopsis",
    "thesis",
)

SI_UNINFLECTED: frozenset[str] = frozenset(
    {
        "status",
        "apparatus",
        "prospectus",
        "sinus",
        "hiatus",
        "impetus",
        "plexus",
        "species",
        "series",
        "news",
        "diabetes",
        "rabies",
        "corps",
        "debris",
        "shears",
        "pliers",
        "scissors",
        "trousers",
        "breeches",
        "headquarters",
        "fish",
        "sheep",
        "moose",
        "bison",
        "buffalo",
        "cattle",
        "swine",
        "salmon",
        "trout",
        "cod",
        "carp",
        "elk",
        "aircraft",
        "metadata",
    }
)


def _plural_from_singular(singular: str, plural_suffix: str, trim: int) -> str:
    return singular[:-trim] + plural_suffix


def _build_pattern_pairs() -> dict[str, str]:
    pairs: dict[str, str] = {}

    def add(singular: str, plural: str) -> None:
        pairs[plural] = singular

    for word in _UM_A_SINGULARS:
        add(word, _plural_from_singular(word, "a", 2))
    for word in _US_I_SINGULARS:
        add(word, _plural_from_singular(word, "i", 2))
    for word in _ON_A_SINGULARS:
        add(word, _plural_from_singular(word, "a", 2))
    for word in _EX_IX_ICES_SINGULARS:
        add(word, _plural_from_singular(word, "ices", 2))
    for word in _IS_IDES_SINGULARS:
        add(word, _plural_from_singular(word, "ides", 2))
    for word in _A_ATA_SINGULARS:
        add(word, _plural_from_singular(word, "ata", 1))
    for word in _EN_INA_SINGULARS:
        add(word, _plural_from_singular(word, "ina", 2))
    for singular, plural in _VES_VE_SINGULARS.items():
        add(singular, plural)
    for word in _ES_IS_SINGULARS:
        add(word, word[:-2] + "es")

    add("basis", "bases")

    return pairs


SI_SB_IRREGULAR: dict[str, str] = _build_si_sb_irregular()
SI_PATTERN_PAIRS: dict[str, str] = _build_pattern_pairs()

_EXTRA_IRREGULAR: dict[str, str] = {
    "people": "person",
    "men": "man",
    "women": "woman",
    "mice": "mouse",
    "geese": "goose",
    "teeth": "tooth",
    "feet": "foot",
}

PLURAL_TO_SINGULAR: dict[str, str] = {
    **{key.lower(): value for key, value in SI_PATTERN_PAIRS.items()},
    **{key.lower(): value for key, value in SI_SB_IRREGULAR.items()},
    **{key.lower(): value for key, value in _EXTRA_IRREGULAR.items()},
}
