-- repo_name: TestRepo

-- name: basic_projection :one
WITH rated_authors AS (
    SELECT a.id, a.rating
    FROM authors a
)
SELECT rated_authors.id
FROM rated_authors;

-- name: chained_ctes :one
WITH author_base AS (
    SELECT a.id, a.name
    FROM authors a
),
book_titles AS (
    SELECT b.author_id, b.title
    FROM books b
)
SELECT ab.name AS author_name, bt.title AS book_title
FROM author_base ab
JOIN book_titles bt ON bt.author_id = ab.id;

-- name: count :one
WITH counts AS (
    SELECT count(*) FROM authors
)
SELECT * from counts;
