-- repo_name: TestRepo

-- name: GetBars :many
SELECT DISTINCT ON (a.id) a.*
FROM bar a;
