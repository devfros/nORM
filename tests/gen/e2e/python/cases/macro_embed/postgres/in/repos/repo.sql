-- repo_name: Repo

-- name: non_null :many
SELECT
  a.*, n.embed(b)
FROM authors a
JOIN books b ON b.author_id = a.id;

-- name: nullable :many
SELECT
  a.*, n.nembed(b)
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;

-- name: embed_and_nembed :many
SELECT
  n.embed(a), n.nembed(b)
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;

-- name: aliased :many
SELECT
  n.embed(a) AS foo, n.nembed(b) AS bar
FROM authors a
LEFT JOIN books b ON b.author_id = a.id;
