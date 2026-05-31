-- repo_name: Repo

-- name: ManyFoo :many
-- This function returns a list of Foos
-- Second line
SELECT * FROM foo;

-- name: OneFoo :one
-- This function returns one Foo
SELECT * FROM foo;

-- name: ExecFoo :exec
-- This function creates a Foo via :exec
INSERT INTO foo (bar) VALUES ('bar');

-- name: ExecRowFoo :execrows
-- This function creates a Foo via :execrows
INSERT INTO foo (bar) VALUES ('bar');
