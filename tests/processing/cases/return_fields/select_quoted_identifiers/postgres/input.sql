-- repo_name: TestRepo

-- name: quoted_alias :one
SELECT a.id AS "AuthorID"
FROM authors a;

-- name: quoted_column_identifier :one
SELECT a."name" AS quoted_name
FROM authors a;

-- name: quoted_table_identifier :one
SELECT "authors".id
FROM "authors";
