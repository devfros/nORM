-- repo_name: TestRepo

-- name: cte_wildcard :one
WITH author_names AS (
    SELECT a.id, a.name
    FROM authors a
)
SELECT * FROM author_names;

-- name: mixed_wildcard_explicit :one
SELECT a.*, b.title FROM authors a JOIN books b ON b.author_id = a.id;

-- name: nested_cte_wildcard :one
WITH all_authors AS (
    SELECT * FROM authors
)
SELECT * FROM all_authors;

-- name: star_single_table :one
SELECT * FROM authors a;

-- name: star_with_join :one
SELECT * FROM authors a JOIN books b ON b.author_id = a.id;

-- name: subquery_wildcard :one
SELECT * FROM (
    SELECT b.id, b.title
    FROM books b
) sub;

-- name: table_wildcard :one
SELECT b.* FROM books b;

-- name: union_wildcard :one
SELECT a.id, a.name FROM authors a
UNION ALL
SELECT * FROM (SELECT b.id, b.title AS name FROM books b) sub;
