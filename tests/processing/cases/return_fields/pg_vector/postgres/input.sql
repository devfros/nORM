-- repo_name: TestRepo

-- name: NearestNeighbor :many
SELECT *
FROM items
ORDER BY embedding <-> :embedding
LIMIT 5;
