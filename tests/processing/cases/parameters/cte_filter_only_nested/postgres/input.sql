-- repo_name: TestRepo

-- name: main :one
WITH filtered AS (
  SELECT year
  FROM books b2
  WHERE b2.title LIKE :title
)
SELECT *
FROM books b
WHERE b.year IN (SELECT year FROM filtered);
