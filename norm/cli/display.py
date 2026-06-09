from __future__ import annotations

import json
import os
import sys
import traceback
from collections.abc import Iterable
from difflib import unified_diff
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from norm.cli.context import CliContext, ErrorFormat
from norm.cli.redact import redact_context
from norm.errors import NormError, NormErrorCode

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from norm.cli.context import CliContext

DIFF_MAX_LINES = 40


def get_console(ctx: CliContext) -> Console:
    no_color = ctx.no_color or bool(os.environ.get("NO_COLOR"))
    return Console(stderr=True, no_color=no_color)


def _format_location(context: dict[str, object]) -> str | None:
    repository = context.get("repository") or context.get("file")
    query = context.get("query") or context.get("query_name")
    line = context.get("line")
    if repository is None and query is None:
        return None
    parts: list[str] = []
    if repository:
        parts.append(str(repository))
    if query:
        parts.append(f"query {query}")
    location = " → ".join(parts) if parts else ""
    if line is not None:
        location = f"{location} (line {line})" if location else f"line {line}"
    return f"  at {location}" if location else None


def _render_inference_issues(console: Console, issues: object) -> None:
    if not isinstance(issues, list):
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("Kind")
    table.add_column("Placeholder")
    table.add_column("Context")
    table.add_column("Message")
    for item in issues:
        if not isinstance(item, dict):
            continue
        table.add_row(
            str(item.get("kind", "")),
            str(item.get("placeholder", "")),
            str(item.get("context", "")),
            str(item.get("message", "")),
        )
    console.print(table)


def _render_config_tree(console: Console, details: object) -> None:
    if not isinstance(details, str):
        return
    tree = Tree("Configuration")
    for line in details.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped:
            loc, _, msg = stripped.partition(":")
            tree.add(f"[bold]{loc.strip()}[/bold]: {msg.strip()}")
        else:
            tree.add(stripped)
    console.print(tree)


def _render_sql_snippet(
    console: Console,
    query: object,
    *,
    start_line: int | None = None,
) -> None:
    if not isinstance(query, str):
        return
    kwargs: dict[str, object] = {"line_numbers": True}
    if start_line is not None:
        kwargs["start_line"] = start_line
    console.print(Syntax(query, "sql", theme="monokai", **kwargs))  # pyright: ignore[reportArgumentType]


def render_error_human(console: Console, err: NormError) -> None:
    context = redact_context(err.context)
    title = f"[bold red]{err.code}[/bold red]"
    console.print(Panel(err.message, title=title, border_style="red"))
    location = _format_location(context)
    if location:
        console.print(location, style="dim")
    if err.hint:
        console.print(f"Hint: {err.hint}", style="yellow")
    if err.code == NormErrorCode.TYPE_INFERENCE_FAILED and "issues" in context:
        _render_inference_issues(console, context["issues"])
    elif err.code == NormErrorCode.INVALID_CONFIG and "details" in context:
        _render_config_tree(console, context["details"])
    elif "query" in context and isinstance(context["query"], str):
        sql_start_line = context.get("sql_start_line")
        start_line = sql_start_line if isinstance(sql_start_line, int) else None
        if start_line is None:
            line = context.get("line")
            start_line = line if isinstance(line, int) else None
        _render_sql_snippet(console, context["query"], start_line=start_line)
    else:
        for key, value in context.items():
            if key in {"issues", "details", "query"}:
                continue
            console.print(f"{key}: {value}")


def render_error_json(err: NormError) -> None:
    payload = {
        "code": str(err.code),
        "message": err.message,
        "hint": err.hint,
        "context": redact_context(err.context),
    }
    sys.stdout.write(json.dumps(payload, default=str) + "\n")


def render_error_github(err: NormError) -> None:
    context = redact_context(err.context)
    file_path = context.get("repository") or context.get("file") or ""
    line = context.get("line", 1)
    title = str(err.code)
    message = err.message
    if err.hint:
        message = f"{message} - {err.hint}"
    location = _format_location(context)
    if location:
        message = f"{message}\n{location.strip()}"
    file_attr = f"file={file_path}," if file_path else ""
    sys.stdout.write(f"::error {file_attr}line={line},title={title}::{message}\n")


def render_error(err: NormError, ctx: CliContext) -> None:
    if ctx.error_format == ErrorFormat.JSON:
        render_error_json(err)
        return
    if ctx.error_format == ErrorFormat.GITHUB:
        render_error_github(err)
        return
    render_error_human(get_console(ctx), err)


def render_unexpected_error(err: Exception, ctx: CliContext) -> None:
    if ctx.error_format == ErrorFormat.JSON:
        payload = {
            "code": "UNEXPECTED",
            "message": str(err),
            "hint": None,
            "context": {"type": type(err).__name__},
        }
        sys.stdout.write(json.dumps(payload) + "\n")
        return
    console = get_console(ctx)
    console.print("[red][Error][/red] Unexpected failure.")
    console.print(f"type: {type(err).__name__}")
    console.print(f"message: {err}")
    if ctx.verbose >= 2:
        console.print(traceback.format_exc())


def print_success(ctx: CliContext, message: str) -> None:
    if ctx.quiet:
        return
    get_console(ctx).print(message, style="bold green")


def print_info(ctx: CliContext, message: str, *, style: str = "") -> None:
    if ctx.quiet:
        return
    console = get_console(ctx)
    if style:
        console.print(message, style=style)
    else:
        console.print(message)


def print_warning(ctx: CliContext, message: str) -> None:
    if ctx.quiet:
        return
    get_console(ctx).print(message, style="bold yellow")


def print_target_action(ctx: CliContext, action: str, target_name: str) -> None:
    if ctx.quiet or ctx.verbose == 0:
        return
    print_info(ctx, f"{action} target: '{target_name}'", style="bold white")


def print_generate_success(
    ctx: CliContext,
    target_name: str,
    out_path: Path,
    files_written: int,
    duration_ms: int,
) -> None:
    if ctx.quiet:
        return
    rel = _relative_path(ctx.base_dir, out_path)
    get_console(ctx).print(
        f"✓ {target_name}: wrote {files_written} files to {rel} ({duration_ms}ms)",
        style="bold green",
    )


def print_schema_pull_success(
    ctx: CliContext,
    target_name: str,
    schema_path: Path,
    line_count: int,
    duration_ms: int,
) -> None:
    if ctx.quiet:
        return
    rel = _relative_path(ctx.base_dir, schema_path)
    get_console(ctx).print(
        f"✓ {target_name}: wrote schema to {rel} ({line_count} lines, {duration_ms}ms)",
        style="bold green",
    )


def print_check_up_to_date(
    ctx: CliContext,
    target_name: str,
    checked_files: int,
) -> None:
    if ctx.quiet:
        return
    get_console(ctx).print(
        f"Target '{target_name}' is up to date ({checked_files} file(s) checked).",
        style="bold green",
    )


def print_check_outdated(
    ctx: CliContext,
    target_name: str,
    outdated_paths: Iterable[Path],
) -> None:
    if ctx.quiet:
        return
    paths = list(outdated_paths)
    console = get_console(ctx)
    console.print(
        f"Target '{target_name}' is out of date ({len(paths)} stale file(s)).",
        style="bold red",
    )
    for path in paths:
        console.print(f"  {path}")


def print_file_diff(
    ctx: CliContext,
    rel_path: Path,
    expected: str,
    current: str,
) -> None:
    if ctx.quiet:
        return
    console = get_console(ctx)
    console.print(f"\n--- {rel_path}", style="bold")
    diff_lines = list(
        unified_diff(
            current.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile="current",
            tofile="expected",
        )
    )
    if len(diff_lines) > DIFF_MAX_LINES:
        diff_lines = diff_lines[:DIFF_MAX_LINES]
        diff_lines.append("… truncated\n")
    console.print("".join(diff_lines), style="dim")


def print_path_tree(ctx: CliContext, title: str, paths: Iterable[Path]) -> None:
    if ctx.quiet:
        return
    tree = Tree(title)
    for path in paths:
        tree.add(str(path))
    get_console(ctx).print(tree)


def _relative_path(base_dir: Path, path: Path) -> str:
    try:
        return f"./{path.resolve().relative_to(base_dir.resolve())}"
    except ValueError:
        return str(path)
