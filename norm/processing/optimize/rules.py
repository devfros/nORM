from sqlglot.optimizer.optimizer import OptimizerFn
from sqlglot.optimizer.qualify import qualify

from .annotate_dml_types import annotate_dml_types
from .annotate_types import annotate_types
from .inference.nullability.engine import infer_placeholder_nullability
from .inference.types.engine import infer_placeholder_types

RULES: tuple[OptimizerFn, ...] = (
    qualify,
    annotate_types,
    annotate_dml_types,
    infer_placeholder_types,
    infer_placeholder_nullability,
)
