-- repo_name: TestRepo

-- name: aliased_column :one
SELECT a.name AS author_name FROM authors a;

-- name: duplicate_projections :one
SELECT a.id, b.id FROM authors a JOIN books b ON b.author_id = a.id;

-- name: qualified_column :one
SELECT a.id FROM authors a;

-- name: unqualified_single_table :one
SELECT id FROM authors;

-- name: unqualified_unique_multitable :one
SELECT title FROM authors a JOIN books b ON b.author_id = a.id;
