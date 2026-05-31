-- repo_name: TestRepo

-- name: main :one
SELECT * FROM books b
JOIN authors a ON a.id = b.author_id
WHERE a.id = :author_id;
