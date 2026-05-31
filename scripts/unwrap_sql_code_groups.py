#!/usr/bin/env python3
"""Remove code-groups from SQL-only blocks; keep groups for generated code."""

from __future__ import annotations

import re
from pathlib import Path

STUBS = """
```go [example.go]
// coming soon
```

```rust [example.rs]
// coming soon
```

```typescript [example.ts]
// coming soon
```
""".strip()

BLOCK_RE = re.compile(
    r"```(?P<lang>[\w.+-]+)(?:\s+\[(?P<title>[^\]]+)\])?\n(?P<body>.*?)\n```",
    re.DOTALL,
)
GROUP_RE = re.compile(r"::: code-group\n\n(.*?)\n:::\n", re.DOTALL)


def blocks_from_inner(inner: str) -> list[tuple[str, str, str | None]]:
    out: list[tuple[str, str, str | None]] = []
    for m in BLOCK_RE.finditer(inner):
        lang = m.group("lang")
        if lang in {"go", "rust", "typescript", "ts"}:
            continue
        title = m.group("title")
        body = m.group("body")
        out.append((lang, body, title))
    return out


def render_block(lang: str, body: str, title: str | None) -> str:
    label = f" [{title}]" if title else ""
    return f"```{lang}{label}\n{body}\n```"


def process_group(inner: str) -> str:
    raw_blocks = list(BLOCK_RE.finditer(inner))
    langs = [m.group("lang") for m in raw_blocks]

    has_sql = "sql" in langs
    has_python = "python" in langs

    if has_sql and not has_python:
        sql = next(m for m in raw_blocks if m.group("lang") == "sql")
        return render_block("sql", sql.group("body"), sql.group("title")) + "\n"

    if has_sql and has_python:
        sql_parts = [
            render_block(m.group("lang"), m.group("body"), m.group("title"))
            for m in raw_blocks
            if m.group("lang") == "sql"
        ]
        py_parts = [
            render_block(m.group("lang"), m.group("body"), m.group("title"))
            for m in raw_blocks
            if m.group("lang") == "python"
        ]
        return (
            "\n\n".join(sql_parts)
            + "\n\n::: code-group\n\n"
            + "\n\n".join(py_parts)
            + "\n\n"
            + STUBS
            + "\n\n:::\n"
        )

    return "::: code-group\n\n" + inner.strip() + "\n\n" + STUBS + "\n\n:::\n"


def process_file(path: Path) -> bool:
    text = path.read_text()
    original = text

    def repl(match: re.Match[str]) -> str:
        return process_group(match.group(1))

    # Groups that already end with stubs in inner - avoid duplicating
    def repl_safe(match: re.Match[str]) -> str:
        inner = match.group(1)
        if "// coming soon" in inner and "python" in inner:
            # may already have stubs inside; strip stubs from inner first
            inner_clean = inner
            for stub_lang in ("go", "rust", "typescript"):
                inner_clean = re.sub(
                    rf"\n```{{1,3}}{stub_lang}.*?\n```\n",
                    "\n",
                    inner_clean,
                    flags=re.DOTALL,
                )
            result = process_group(inner_clean)
            return result
        return process_group(inner)

    new = GROUP_RE.sub(repl_safe, text)
    if new != original:
        path.write_text(new)
        return True
    return False


def main() -> None:
    roots = [
        Path("docs/guides"),
        Path("docs/reference/annotations.md"),
        Path("docs/reference/macros.md"),
        Path("docs/reference/configuration/python.md"),
        Path("docs/overview/what-is-norm.md"),
        Path("docs/tutorials/python.md"),
    ]
    for root in roots:
        paths = sorted(root.glob("*.md")) if root.is_dir() else [root]
        for path in paths:
            if process_file(path):
                print("fixed", path)


if __name__ == "__main__":
    main()
