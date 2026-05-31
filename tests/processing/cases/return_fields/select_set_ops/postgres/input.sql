-- repo_name: TestRepo

-- name: except_basic :one
SELECT a.id
FROM authors a
EXCEPT
SELECT b.author_id
FROM books b;

-- name: intersect_basic :one
SELECT a.id
FROM authors a
INTERSECT
SELECT b.author_id
FROM books b;

-- name: parenthesized_union_wrapper :one
SELECT u.id
FROM (
    (SELECT a.id FROM authors a)
    UNION
    (SELECT b.author_id AS id FROM books b)
) u;

-- name: union_alias :one
SELECT id AS entity_id FROM authors
UNION
SELECT id AS entity_id FROM books;

-- name: union_all_text :one
SELECT name AS value FROM authors
UNION ALL
SELECT title AS value FROM books;

-- name: union_cast_text :one
SELECT CAST(id AS TEXT) AS value FROM authors
UNION
SELECT isbn AS value FROM books;
