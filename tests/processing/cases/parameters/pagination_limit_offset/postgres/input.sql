-- repo_name: TestRepo

-- name: main :one
SELECT * FROM authors LIMIT :limit OFFSET :offset;
