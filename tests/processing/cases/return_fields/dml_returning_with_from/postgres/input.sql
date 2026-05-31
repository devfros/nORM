-- repo_name: TestRepo

-- name: update_from_returning_join_col :one
UPDATE authors a
SET rating = a.rating + 1
FROM books b
WHERE b.author_id = a.id
RETURNING a.id AS author_id, b.title AS matched_title;
