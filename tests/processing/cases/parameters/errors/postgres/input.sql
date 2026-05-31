-- repo_name: TestRepo

-- name: derived_missing_alias :one
SELECT *
FROM (
  SELECT a.id AS known_id
  FROM authors a
) d
WHERE :p = d.unknown_id;

-- name: unknown_alias :one
SELECT a.id
FROM authors a
WHERE :p = x.id;
