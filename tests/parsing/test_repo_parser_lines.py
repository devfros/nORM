import pytest
from sqlglot import Dialects

from norm.errors import NormError, NormErrorCode
from norm.parsing import RepoSqlParser


def _parse_repo(sql: str):
    return RepoSqlParser(Dialects.POSTGRES).parse_sql(sql)


def test_sql_start_line_immediately_after_annotation():
    sql = """-- repo_name: Repo

-- name: GetOne :one
SELECT 1;
"""
    repo = _parse_repo(sql)
    assert repo is not None
    assert len(repo.queries) == 1
    assert repo.queries[0].line == 3
    assert repo.queries[0].sql_start_line == 4


def test_sql_start_line_skips_doc_comments():
    sql = """-- repo_name: Repo

-- name: GetOne :one
-- doc comment
-- more doc
SELECT 1;
"""
    repo = _parse_repo(sql)
    assert repo is not None
    assert repo.queries[0].sql_start_line == 6


def test_sql_start_line_skips_blank_lines():
    sql = """-- repo_name: Repo

-- name: GetOne :one
-- doc comment

SELECT 1;
"""
    repo = _parse_repo(sql)
    assert repo is not None
    assert repo.queries[0].sql_start_line == 6


def test_sql_start_line_skips_block_doc_comment():
    sql = """-- repo_name: Repo

-- name: GetOne :one
/* block doc */
SELECT 1;
"""
    repo = _parse_repo(sql)
    assert repo is not None
    assert repo.queries[0].sql_start_line == 5
    assert repo.queries[0].comment == "block doc"


def test_sql_start_line_keeps_optimizer_hint():
    sql = """-- repo_name: Repo

-- name: GetOne :one
/*+ SeqScan(t) */
SELECT 1;
"""
    repo = _parse_repo(sql)
    assert repo is not None
    assert repo.queries[0].sql_start_line == 4


def test_parse_error_reports_exact_file_line():
    sql = """-- repo_name: Repo

-- name: BadQuery :one
-- doc comment

SELECT bad FROM
"""
    with pytest.raises(NormError) as exc_info:
        _parse_repo(sql)

    err = exc_info.value
    assert err.code == NormErrorCode.SQL_PARSE_FAILED
    assert err.context["query"] == "BadQuery"
    assert err.context["sql_start_line"] == 6
    assert err.context["line"] == 6
    assert "Line 6" in str(err.context["details"])
