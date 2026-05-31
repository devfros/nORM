-- repo_name: TestRepo

-- name: exists_correlated_flag :one
SELECT
    EXISTS (SELECT 1 FROM books b WHERE b.author_id = a.id) AS has_books
FROM authors a;

-- name: from_derived_table :one
SELECT s.author_id
FROM (
    SELECT b.author_id
    FROM books b
) s;

-- name: in_subquery_flag :one
SELECT (a.id IN (SELECT b.author_id FROM books b)) AS has_books
FROM authors a;

-- name: nested_correlated_exists :one
SELECT (
    EXISTS (
        SELECT 1
        FROM books b
        WHERE b.author_id = a.id
          AND b.id IN (SELECT b2.id FROM books b2 WHERE b2.author_id = a.id)
    )
) AS deeply_has_books
FROM authors a;

-- name: not_in_subquery_flag :one
SELECT (a.id NOT IN (SELECT b.author_id FROM books b)) AS has_no_books
FROM authors a;

-- name: scalar_correlated_count :one
SELECT
    (SELECT COUNT(*) FROM books b WHERE b.author_id = a.id) AS book_count
FROM authors a;

-- name: scalar_uncorrelated :one
SELECT (SELECT COUNT(*) FROM books) AS total_books
FROM authors a;
