-- repo_name: TestRepo

-- name: In :many
SELECT *
FROM bar
WHERE id IN (:id_1, :id_2);
