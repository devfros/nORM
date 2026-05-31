-- repo_name: TestRepo

-- name: delete_using_returning :one
DELETE FROM authors a
USING books b
WHERE b.author_id = a.id
RETURNING a.id AS deleted_author_id, b.title AS related_title;

-- name: delete_using_returning_wildcard :one
DELETE FROM books b
USING authors a
WHERE b.author_id = a.id
RETURNING a.*;
