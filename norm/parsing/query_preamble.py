from dataclasses import dataclass

from sqlglot import Dialects
from sqlglot.dialects.dialect import Dialect


@dataclass(frozen=True)
class QueryPreamble:
    sql_body: str
    comment: str | None
    sql_body_offset: int


def file_line_at_offset(text: str, offset: int, base_line: int) -> int:
    return base_line + text[:offset].count("\n")


def split_query_preamble(text: str, dialect: Dialects) -> QueryPreamble:
    dialect_cls = Dialect.get_or_raise(dialect)
    tokenizer_cls = dialect_cls.tokenizer()
    comment_starts = sorted(
        tokenizer_cls._COMMENTS,  # noqa: SLF001
        key=len,
        reverse=True,
    )
    hint_start = tokenizer_cls.HINT_START
    nested_comments = tokenizer_cls.NESTED_COMMENTS

    pos = 0
    size = len(text)
    doc_parts: list[str] = []

    while pos < size:
        while pos < size and text[pos] in " \t\r\n":
            pos += 1
        if pos >= size:
            break

        if hint_start and text.startswith(hint_start, pos):
            break

        matched = False
        for comment_start in comment_starts:
            if comment_start == hint_start:
                continue
            if not text.startswith(comment_start, pos):
                continue

            comment_end = tokenizer_cls._COMMENTS[comment_start]  # noqa: SLF001
            if comment_end is None:
                line_end = _find_line_end(text, pos)
                body = text[pos + len(comment_start) : line_end].strip()
                if body:
                    doc_parts.append(body)
                pos = line_end
            else:
                end_pos, body = _scan_block_comment(
                    text,
                    pos,
                    comment_start,
                    comment_end,
                    nested_comments,
                )
                if end_pos == pos:
                    matched = False
                    break
                inner = body.strip()
                if inner:
                    doc_parts.append(inner)
                pos = end_pos

            matched = True
            break

        if not matched:
            break

    comment = "\n".join(doc_parts).strip() or None
    sql_body = text[pos:].strip()
    sql_body_offset = pos + (len(text[pos:]) - len(text[pos:].lstrip()))
    if not sql_body:
        sql_body_offset = pos

    return QueryPreamble(
        sql_body=sql_body,
        comment=comment,
        sql_body_offset=sql_body_offset,
    )


def _find_line_end(text: str, pos: int) -> int:
    for index, char in enumerate(text[pos:], start=pos):
        if char in "\r\n":
            return index
    return len(text)


def _scan_block_comment(
    text: str,
    pos: int,
    comment_start: str,
    comment_end: str,
    nested_comments: bool,
) -> tuple[int, str]:
    start_size = len(comment_start)
    end_size = len(comment_end)
    index = pos + start_size
    depth = 1

    while index < len(text):
        if text.startswith(comment_end, index):
            depth -= 1
            if depth == 0:
                body = text[pos + start_size : index]
                return index + end_size, body
            index += end_size
            continue

        if nested_comments and text.startswith(comment_start, index):
            depth += 1
            index += start_size
            continue

        index += 1

    return pos, ""
