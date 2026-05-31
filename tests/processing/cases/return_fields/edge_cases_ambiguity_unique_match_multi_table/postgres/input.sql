-- repo_name: TestRepo

-- name: main :one
SELECT rating FROM authors a JOIN books b ON b.author_id = a.id;
