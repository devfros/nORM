-- repo_name: TestRepo

-- name: InsertVector :exec
INSERT INTO items (embedding) VALUES (:embedding);

-- name: NearestNeighbor :many
SELECT *
FROM items
ORDER BY embedding <-> :embedding
LIMIT 5;
