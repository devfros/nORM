from sqlglot import Dialects

from norm.parsing.query_preamble import file_line_at_offset, split_query_preamble


def test_split_strips_block_doc_comment():
    text = "/* block doc */\nSELECT 1"
    preamble = split_query_preamble(text, Dialects.POSTGRES)
    assert preamble.comment == "block doc"
    assert preamble.sql_body == "SELECT 1"
    assert preamble.sql_body_offset == text.index("SELECT")


def test_split_strips_hash_comment_for_mysql():
    text = "# mysql doc\nSELECT 1"
    preamble = split_query_preamble(text, Dialects.MYSQL)
    assert preamble.comment == "mysql doc"
    assert preamble.sql_body == "SELECT 1"


def test_split_keeps_optimizer_hint():
    text = "/*+ USE_NL(t) */\nSELECT * FROM t"
    preamble = split_query_preamble(text, Dialects.MYSQL)
    assert preamble.comment is None
    assert preamble.sql_body.startswith("/*+ USE_NL(t) */")
    assert preamble.sql_body_offset == 0


def test_split_multiline_block_doc():
    text = "/*\n * multi\n * line\n */\nSELECT 1"
    preamble = split_query_preamble(text, Dialects.POSTGRES)
    assert preamble.comment is not None
    assert "multi" in preamble.comment
    assert preamble.sql_body == "SELECT 1"


def test_file_line_at_offset():
    text = "\n-- doc\n\nSELECT 1"
    assert file_line_at_offset(text, text.index("SELECT"), base_line=3) == 6
