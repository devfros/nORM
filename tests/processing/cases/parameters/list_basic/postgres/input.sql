-- repo_name: TestRepo

-- name: main :one
SELECT * FROM authors WHERE id IN (n.list(:ids));
