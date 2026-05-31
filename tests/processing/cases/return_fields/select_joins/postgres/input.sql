-- repo_name: TestRepo

-- name: cross_join_projection :one
SELECT a.id, b.title
FROM authors a
CROSS JOIN books b;

-- name: full_join_projection :one
SELECT a.id, b.id AS book_id
FROM authors a
FULL JOIN books b ON b.author_id = a.id;

-- name: left_join_projection :one
SELECT a.id, b.title
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;

-- name: right_join_projection :one
SELECT a.id, b.id AS book_id
FROM authors a
RIGHT JOIN books b ON b.author_id = a.id;
