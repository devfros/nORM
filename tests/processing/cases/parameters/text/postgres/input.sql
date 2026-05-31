-- repo_name: TestRepo

-- name: like :one
SELECT * FROM books WHERE title LIKE :pattern;

-- name: ilike :one
SELECT * FROM books WHERE title ILIKE :pattern;

-- name: concat :one
SELECT * FROM authors WHERE name = :first || :last;
