from __future__ import annotations

from dataclasses import dataclass

from norm.errors import NormError, NormErrorCode


@dataclass(frozen=True)
class GenerateWorkerOutcome:
    target_name: str
    success: bool
    files_written: int = 0
    duration_ms: int = 0
    error_code: str | None = None
    message: str | None = None
    hint: str | None = None
    context: dict[str, str] | None = None


def _picklable_context(context: dict[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in context.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                result[f"{key}.{nested_key}"] = str(nested_value)
        elif isinstance(value, list):
            result[key] = ", ".join(str(item) for item in value)
        else:
            result[key] = str(value)
    return result


def _failure_outcome(target_name: str, err: NormError) -> GenerateWorkerOutcome:
    context = _picklable_context(err.context)
    context.setdefault("target", target_name)
    return GenerateWorkerOutcome(
        target_name=target_name,
        success=False,
        error_code=str(err.code),
        message=err.message,
        hint=err.hint,
        context=context,
    )


def raise_from_worker_outcome(outcome: GenerateWorkerOutcome) -> None:
    if outcome.success:
        return
    try:
        code = NormErrorCode(outcome.error_code)
    except (ValueError, TypeError):
        code = NormErrorCode.INVALID_CONFIG
    raise NormError(
        code=code,
        message=outcome.message or "Generation failed.",
        hint=outcome.hint,
        context=dict(outcome.context or {}),
    )


def generate_target_worker(
    config_path: str,
    base_dir: str,
    target_name: str,
) -> GenerateWorkerOutcome:
    from pathlib import Path

    from norm.cli.context import target_path
    from norm.cli.gen import create_generated_content, generate_target
    from norm.config import load_norm_config

    try:
        config = load_norm_config(config_path)
        target = config.targets[target_name]
        root = Path(base_dir)
        output, stats = generate_target(target, base_dir=root, verbose=0)
        out_path = target_path(root, target.gen.out)
        files_written = create_generated_content(out_path, output)
        return GenerateWorkerOutcome(
            target_name=target_name,
            success=True,
            files_written=files_written,
            duration_ms=stats.duration_ms,
        )
    except NormError as err:
        return _failure_outcome(target_name, err)
    except Exception as err:
        return GenerateWorkerOutcome(
            target_name=target_name,
            success=False,
            error_code=str(NormErrorCode.INVALID_CONFIG),
            message=str(err),
            hint="Run with -v or --target for a detailed error in the main process.",
            context={"target": target_name, "type": type(err).__name__},
        )
