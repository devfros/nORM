-- repo_name: Repo

-- name: FullJoin :many
SELECT f.id, f.bar_id, b.id
FROM foo f
FULL OUTER JOIN bar b ON b.id = f.bar_id
WHERE f.id = :id;
