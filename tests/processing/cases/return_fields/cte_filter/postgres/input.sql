-- repo_name: TestRepo

-- name: CTEFilter :many
WITH filter_count AS (
    SELECT count(*) FROM bar WHERE ready = :ready
)
SELECT filter_count.count
FROM filter_count;
