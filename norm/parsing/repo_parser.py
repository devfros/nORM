import re
from pathlib import Path

from sqlglot import Dialects, parse
from sqlglot.errors import ParseError
from sqlglot.expressions import Delete, Insert, Select, Update

from norm.errors import NormError, NormErrorCode
from norm.schemas.repo import QueryCommandEnum, Repo, RepoQuery


class RepoSqlParser:
    """Parse repository `.sql` files into a `Repo`."""

    def __init__(self, dialect: Dialects) -> None:
        self._dialect = dialect

    def parse_file(self, file_path: str | Path) -> Repo | None:
        file_path = Path(file_path)
        with file_path.open(mode="r") as sql_file:
            content = sql_file.read()

        return self.parse_sql(content, file_path=file_path)

    def parse_sql(
        self,
        content: str,
        *,
        file_path: str | Path | None = None,
    ) -> Repo | None:
        if content is None or len(content) == 0:
            return None

        resolved_path = Path(file_path) if file_path is not None else Path("<string>")

        queries: list[tuple[str, str, int]] = []
        query_pattern = re.compile(r"^-- (name:.*)$", re.MULTILINE)
        matches = list(query_pattern.finditer(content))

        for i, match in enumerate(matches):
            annotation = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            query_text = content[start:end].strip()
            line = content.count("\n", 0, match.start()) + 1
            queries.append((annotation, query_text, line))

        header = content[: matches[0].start()] if matches else content
        repo_match = re.search(r"^-- (repo_name:.*)$", header, re.MULTILINE)
        repo_annotation = repo_match.group(1) if repo_match else None

        repo_name = self._repo_name_from_annotation(repo_annotation)

        repo = Repo(
            name=repo_name,
            file_path=resolved_path,
            queries=[],
            processed_queries=[],
        )

        visited: set[str] = set()
        for query_annotation, query_content, query_line in queries:
            name, command = self._query_name_and_command_from_annotation(
                query_annotation
            )
            if name in visited:
                raise NormError(
                    code=NormErrorCode.DUPLICATE_QUERY,
                    message=f"Duplicate query '{name}'.",
                    context={
                        "query_name": name,
                        "repository": resolved_path.name,
                        "query": name,
                        "line": query_line,
                    },
                )
            visited.add(name)

            try:
                query_sql, comment = _split_leading_query_comment(query_content)
                parsed = parse(query_sql, dialect=self._dialect)

                if parsed is None or len(parsed) == 0:
                    continue

                query = parsed[0]

                if (
                    all(
                        isinstance(query, query_type)
                        for query_type in [Select, Insert, Update, Delete]
                    )
                    or query is None
                ):
                    continue

                query.pop_comments()

                for n in query.dfs():
                    n.pop_comments()

                repo_query = RepoQuery(
                    name=name,
                    command=command,
                    sql=query,  # pyright: ignore[reportArgumentType]
                    comment=comment,
                    line=query_line,
                )
                repo.queries.append(repo_query)
            except ParseError as err:
                raise NormError(
                    code=NormErrorCode.SQL_PARSE_FAILED,
                    message=f"Failed to parse repository SQL file '{resolved_path.name}'.",
                    hint="Fix SQL syntax errors in repository queries and rerun.",
                    context={
                        "repository": resolved_path.name,
                        "file": str(resolved_path),
                        "details": str(err),
                    },
                ) from err

        return repo

    def _repo_name_from_annotation(self, repo_annotation: str | None) -> str:
        if not repo_annotation:
            raise NormError(
                code=NormErrorCode.MISSING_ANNOTATION,
                message="Missing repository annotation on the first query.",
            )

        annotation = repo_annotation.strip()

        pattern = r"^(repo_name*:\s*\w*)"
        result = re.match(pattern, annotation)

        if result is None:
            raise NormError(
                code=NormErrorCode.INVALID_ANNOTATION,
                message="Invalid repository annotation: repo name is missing.",
                context={"annotation": annotation},
            )

        repo_name = annotation.split(":")[1].strip()
        return repo_name

    def _query_name_and_command_from_annotation(
        self,
        query_annotation: str | None,
    ) -> tuple[str, QueryCommandEnum]:
        if not query_annotation:
            raise NormError(
                code=NormErrorCode.MISSING_ANNOTATION,
                message="Missing query annotation.",
                hint="Add '-- name: query_name :one/:many/etc..' before the query.",
            )

        pattern = r"^(name*:\s*\w*)\s*(:\w*)"
        result = re.match(pattern, query_annotation)

        if result is None:
            raise NormError(
                code=NormErrorCode.INVALID_ANNOTATION,
                message="Invalid query annotation",
                hint="Use '-- name: query_name :one/:many/etc..'.",
                context={"annotation": query_annotation},
            )

        name_annotation = result.group(1)
        command_annotation = result.group(2)

        name = name_annotation.split(":")[1].strip()
        command_str = command_annotation[1:]

        try:
            command = QueryCommandEnum(command_annotation[1:])
        except ValueError as err:
            raise NormError(
                code=NormErrorCode.INVALID_ANNOTATION,
                message=f"Invalid query command '{command_str}'.",
                context={"query_name": name, "command": command_str},
            ) from err

        return name, command


def _split_leading_query_comment(query_text: str) -> tuple[str, str | None]:
    comment_lines: list[str] = []
    sql_lines: list[str] = []
    reading_comment = True

    for line in query_text.splitlines():
        stripped = line.strip()
        if reading_comment and stripped.startswith("--"):
            comment_lines.append(stripped[2:].strip())
            continue

        if reading_comment and not stripped:
            continue

        reading_comment = False
        sql_lines.append(line)

    comment = "\n".join(comment_lines).strip() or None
    return "\n".join(sql_lines).strip(), comment
