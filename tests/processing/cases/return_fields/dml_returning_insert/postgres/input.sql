-- repo_name: TestRepo

-- name: basic :one
INSERT INTO authors (name, rating)
VALUES ('Alice', 5)
RETURNING id, name;

-- name: expression_alias :one
INSERT INTO authors (name, rating)
VALUES ('Alice', 5)
RETURNING id AS author_id, rating + 1 AS next_rating;

-- name: insert_select_returning :one
INSERT INTO authors (name, rating)
SELECT b.title, b.year
FROM books b
RETURNING id, name;

-- name: no_returning :one
INSERT INTO authors (name, rating) VALUES ('A', 5);
