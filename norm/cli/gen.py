from __future__ import annotations

import multiprocessing
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from norm.cli.context import CliContext, load_config, target_path
from norm.cli.display import (
    print_check_outdated,
    print_check_up_to_date,
    print_file_diff,
    print_generate_success,
    print_target_action,
    print_warning,
)
from norm.cli.options import pass_cli_context, target_option
from norm.cli.workers import (
    GenerateWorkerOutcome,
    raise_from_worker_outcome,
)
from norm.errors import NormError, NormErrorCode, with_context

if TYPE_CHECKING:
    from pathlib import Path

    from norm.parsing.repo_parser import RepoSqlParser
    from norm.processing.processor import QueryProcessor
    from norm.schemas import GenOutputFiles
    from norm.schemas.config import TargetConfig
    from norm.schemas.repo import Repo

POOL_MAX_WORKERS = 4


def _process_pool_executor(workers: int) -> ProcessPoolExecutor:
    # spawn avoids fork() in a multi-threaded parent (Rich, logging, etc.)
    mp_context = multiprocessing.get_context("spawn")
    return ProcessPoolExecutor(max_workers=workers, mp_context=mp_context)


@dataclass(frozen=True)
class TargetStats:
    repos_parsed: int
    queries_processed: int
    files_written: int
    duration_ms: int


def generate_target(
    target: TargetConfig,
    *,
    base_dir: Path,
    verbose: int = 0,
    action: str = "Generating",
    cli_ctx: CliContext | None = None,
) -> tuple[GenOutputFiles, TargetStats]:
    from sqlglot import Dialects

    from norm.gen.get_generator import get_generator
    from norm.parsing import RepoSqlParser, SchemaSqlParser
    from norm.processing.processor import QueryProcessor

    started = time.perf_counter()
    if cli_ctx is not None and cli_ctx.verbose > 0:
        print_target_action(cli_ctx, action, target.name)

    dialect = Dialects(target.sql.engine)
    schema_path = target_path(base_dir, target.sql.db_schema)
    db_schema = SchemaSqlParser(dialect).parse_file(schema_path)
    if db_schema is None:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Target '{target.name}' has empty or invalid db schema.",
            context={"target": target.name, "db_schema": target.sql.db_schema},
        )

    repos_path = target_path(base_dir, target.sql.repositories)
    discovered_repos: list[Path] = list(repos_path.glob("*.sql", case_sensitive=False))
    if len(discovered_repos) == 0:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Target '{target.name}' has no repository files.",
            context={"target": target.name, "repositories": str(repos_path)},
        )

    repo_parser = RepoSqlParser(dialect)
    parsed_repos: list[Repo] = []
    queries_processed = 0

    if verbose >= 1:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(
                "Parsing repositories", total=len(discovered_repos)
            )
            for item in discovered_repos:
                parsed = _parse_repo(repo_parser, item, target)
                if parsed is not None:
                    parsed_repos.append(parsed)
                    queries_processed += len(parsed.queries)
                progress.advance(task)
    else:
        for item in discovered_repos:
            parsed = _parse_repo(repo_parser, item, target)
            if parsed is not None:
                parsed_repos.append(parsed)
                queries_processed += len(parsed.queries)

    generator = get_generator(target)
    if not generator:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Target '{target.name}' has invalid gen configuration.",
            context={"target": target.name, "details": str(target.gen)},
        )

    invalid_commands = generator.dialect_profile.unsupported_query_commands or {}
    processor = QueryProcessor(db_schema, generator.dialect_profile.param_template)
    processed_repos: list[Repo] = []

    for repo in parsed_repos:
        for repo_query in repo.queries:
            if repo_query.command in invalid_commands:
                raise NormError(
                    code=NormErrorCode.INVALID_QUERY_COMMAND,
                    message=(
                        f"Query command `:{repo_query.command}` is not supported "
                        f"for dialect {dialect.value}"
                    ),
                    context={
                        "target": target.name,
                        "repository": repo.file_path.name,
                        "query": repo_query.name,
                        "line": repo_query.line,
                    },
                )
            try:
                processed_query = processor.process(repo_query)
            except NormError as err:
                raise with_context(
                    err,
                    target=target.name,
                    repository=repo.file_path.name,
                    query=repo_query.name,
                    line=repo_query.line,
                ) from err
            repo.processed_queries.append(processed_query.model_copy(deep=True))
        processed_repos.append(repo)

    output = generator.generate(db_schema, processed_repos)
    file_count = len(list(output.iter_files()))
    duration_ms = int((time.perf_counter() - started) * 1000)
    stats = TargetStats(
        repos_parsed=len(parsed_repos),
        queries_processed=queries_processed,
        files_written=file_count,
        duration_ms=duration_ms,
    )
    return output, stats


def _parse_repo(
    repo_parser: RepoSqlParser,
    item: Path,
    target: TargetConfig,
) -> Repo | None:
    parsed = repo_parser.parse_file(item)
    if parsed is None:
        raise NormError(
            code=NormErrorCode.SQL_PARSE_FAILED,
            message=f"Couldn't parse repository '{item.name}'.",
            context={
                "target": target.name,
                "repository": item.name,
            },
        )
    return parsed


def create_generated_content(out_path: Path, content: GenOutputFiles) -> int:
    if out_path.exists():
        shutil.rmtree(out_path)
    content.create(out_path)
    return len(list(content.iter_files()))


def check_generated_content(
    out_path: Path,
    content: GenOutputFiles,
) -> tuple[int, list[Path], dict[Path, tuple[str, str]]]:
    outdated_paths: list[Path] = []
    diff_contents: dict[Path, tuple[str, str]] = {}
    checked_files = 0

    for rel_path, expected_content in content.iter_files():
        full_path = out_path / rel_path
        if not full_path.is_file():
            continue

        checked_files += 1
        try:
            current_content = full_path.read_text(encoding="utf-8")
        except OSError:
            outdated_paths.append(rel_path)
            diff_contents[rel_path] = ("", expected_content)
            continue

        if current_content != expected_content:
            outdated_paths.append(rel_path)
            diff_contents[rel_path] = (current_content, expected_content)

    return checked_files, outdated_paths, diff_contents


def check_target_sync(
    target: TargetConfig,
    *,
    base_dir: Path,
    verbose: int = 0,
    cli_ctx: CliContext | None = None,
) -> tuple[int, list[Path], dict[Path, tuple[str, str]], TargetStats]:
    generated_content, stats = generate_target(
        target,
        base_dir=base_dir,
        verbose=verbose,
        action="Checking",
        cli_ctx=cli_ctx,
    )
    out_path = target_path(base_dir, target.gen.out)
    checked, outdated, diffs = check_generated_content(out_path, generated_content)
    return checked, outdated, diffs, stats


def _resolve_target_list(
    config: object,
    target: str | None,
) -> list[TargetConfig]:
    from norm.schemas import NormConfig

    assert isinstance(config, NormConfig)
    if target:
        target_config = config.targets.get(target)
        if target_config is None:
            raise NormError(
                code=NormErrorCode.UNKNOWN_TARGET,
                message=f"Target '{target}' is not in config file.",
            )
        return [target_config]
    return list(config.targets.values())


def _run_generate_targets(
    cli_ctx: CliContext,
    targets: list[TargetConfig],
    *,
    parallel: bool = False,
) -> None:
    if parallel and len(targets) > 1:
        _run_generate_parallel(cli_ctx, targets)
        return

    for target_config in targets:
        output, stats = generate_target(
            target_config,
            base_dir=cli_ctx.base_dir,
            verbose=cli_ctx.verbose,
            cli_ctx=cli_ctx,
        )
        out_path = target_path(cli_ctx.base_dir, target_config.gen.out)
        files_written = create_generated_content(out_path, output)
        print_generate_success(
            cli_ctx,
            target_config.name,
            out_path,
            files_written,
            stats.duration_ms,
        )


def _worker_future_result(
    future: object,
    target_name: str,
) -> GenerateWorkerOutcome:
    from concurrent.futures import BrokenExecutor
    from concurrent.futures.process import BrokenProcessPool

    try:
        outcome = future.result()  # type: ignore[union-attr]
    except NormError as err:
        raise with_context(err, target=target_name) from err
    except (BrokenProcessPool, BrokenExecutor) as err:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Generation failed for target '{target_name}'.",
            hint="Run with -v or --target for a detailed error message.",
            context={"target": target_name, "details": str(err)},
        ) from err
    except Exception as err:
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Generation failed for target '{target_name}'.",
            hint="Run with -v or --target for a detailed error message.",
            context={
                "target": target_name,
                "type": type(err).__name__,
                "details": str(err),
            },
        ) from err

    if not isinstance(outcome, GenerateWorkerOutcome):
        raise NormError(
            code=NormErrorCode.INVALID_CONFIG,
            message=f"Generation failed for target '{target_name}'.",
            hint="Run with -v or --target for a detailed error message.",
        )
    return outcome


def _run_generate_parallel(
    cli_ctx: CliContext,
    targets: list[TargetConfig],
) -> None:
    from norm.cli.workers import generate_target_worker

    config_path = str(cli_ctx.config_path)
    base_dir = str(cli_ctx.base_dir)
    workers = min(POOL_MAX_WORKERS, len(targets))
    results: dict[str, GenerateWorkerOutcome] = {}

    with _process_pool_executor(workers) as executor:
        futures = {
            executor.submit(
                generate_target_worker,
                config_path,
                base_dir,
                item.name,
            ): item.name
            for item in targets
        }
        for future in as_completed(futures):
            target_name = futures[future]
            outcome = _worker_future_result(future, target_name)
            if not outcome.success:
                raise_from_worker_outcome(outcome)
            results[outcome.target_name] = outcome

    for name in sorted(results):
        outcome = results[name]
        target_config = next(t for t in targets if t.name == name)
        print_generate_success(
            cli_ctx,
            name,
            target_path(cli_ctx.base_dir, target_config.gen.out),
            outcome.files_written,
            outcome.duration_ms,
        )


GENERATE_EPILOG = """
Examples:

  norm generate
  norm generate --target default
  norm generate -t default
"""


@click.command("generate")
@target_option
@click.option(
    "--parallel",
    is_flag=True,
    help="Generate multiple targets in parallel (one process per target).",
)
@pass_cli_context
def generate(
    cli_ctx: CliContext,
    target: str | None,
    parallel: bool,
) -> None:
    """Generate code for one target or all configured targets."""
    config = load_config(cli_ctx)
    targets = _resolve_target_list(config, target)
    _run_generate_targets(cli_ctx, targets, parallel=parallel)


generate.epilog = GENERATE_EPILOG


CHECK_EPILOG = """
Examples:

  norm check
  norm check --target default --diff
  norm check --fix
  norm check --strict
"""


@click.command("check")
@target_option
@click.option("--diff", is_flag=True, help="Show unified diff for stale files.")
@click.option("--fix", is_flag=True, help="Regenerate stale targets after check.")
@click.option(
    "--strict",
    is_flag=True,
    help="Fail when no generated files exist to compare.",
)
@pass_cli_context
def check(
    cli_ctx: CliContext,
    target: str | None,
    diff: bool,
    fix: bool,
    strict: bool,
) -> None:
    """Check whether generated output is synchronized with current SQL sources."""
    config = load_config(cli_ctx)
    targets = _resolve_target_list(config, target)

    has_failures = False
    has_strict_failures = False
    failure_context: dict[str, list[str]] = {}
    fix_targets: list[TargetConfig] = []

    for target_config in targets:
        checked_files, outdated_paths, diff_contents, _stats = check_target_sync(
            target_config,
            base_dir=cli_ctx.base_dir,
            verbose=cli_ctx.verbose,
            cli_ctx=cli_ctx,
        )

        if len(outdated_paths) > 0:
            has_failures = True
            failure_context[target_config.name] = [str(item) for item in outdated_paths]
            print_check_outdated(cli_ctx, target_config.name, outdated_paths)
            if diff:
                for rel_path in outdated_paths:
                    pair = diff_contents.get(rel_path)
                    if pair is not None:
                        print_file_diff(cli_ctx, rel_path, pair[1], pair[0])
            fix_targets.append(target_config)
            continue

        if checked_files == 0:
            print_warning(
                cli_ctx,
                (
                    f"Target '{target_config.name}' has no existing generated "
                    "files to compare."
                ),
            )
            if strict:
                has_strict_failures = True
            continue

        print_check_up_to_date(cli_ctx, target_config.name, checked_files)

    if has_strict_failures:
        raise NormError(
            code=NormErrorCode.OUTOFDATE,
            message="No generated files found to compare.",
            hint="Run 'norm generate' to create generated output.",
        )

    if has_failures:
        if fix:
            for target_config in fix_targets:
                output, stats = generate_target(
                    target_config,
                    base_dir=cli_ctx.base_dir,
                    verbose=cli_ctx.verbose,
                    cli_ctx=cli_ctx,
                )
                out_path = target_path(cli_ctx.base_dir, target_config.gen.out)
                files_written = create_generated_content(out_path, output)
                print_generate_success(
                    cli_ctx,
                    target_config.name,
                    out_path,
                    files_written,
                    stats.duration_ms,
                )
            return
        raise NormError(
            code=NormErrorCode.OUTOFDATE,
            message="Generated code is out of date.",
            hint="Run 'norm generate' to refresh generated files.",
            context={"targets": failure_context},
        )


check.epilog = CHECK_EPILOG
