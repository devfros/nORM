-- repo_name: TestRepo

-- name: ambiguous_column_authors_books_id :one
SELECT id FROM authors a JOIN books b ON b.author_id = a.id;

-- name: ambiguous_column_self_join_id :one
SELECT id FROM authors a1 JOIN authors a2 ON a1.id <> a2.id;

-- name: ambiguous_column_update_returning_unqualified_id :one
UPDATE authors a
SET rating = a.rating + 1
FROM books b
WHERE b.author_id = a.id
RETURNING id;

-- name: multiple_issues_error_precedence_unknown_alias_first :one
SELECT z.missing_column FROM authors a;

-- name: unknown_column_qualified :one
SELECT a.missing_col FROM authors a;

-- name: unknown_column_unqualified :one
SELECT missing_col FROM authors;

-- name: unknown_table_alias_column_ref :one
SELECT z.id FROM authors a;

-- name: unknown_table_alias_table_wildcard :one
SELECT z.* FROM authors a;

-- name: unknown_table_alias_update_returning_from_alias :one
UPDATE authors a
SET rating = a.rating + 1
FROM books b
WHERE b.author_id = a.id
RETURNING z.id;

-- name: unknown_table_qualified_ref :one
SELECT ghost.id
FROM ghost;
