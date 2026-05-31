-- repo_name: TestRepo

-- name: and_guard :one
SELECT a.id FROM authors a WHERE :left_guard and :right_guard;

-- name: cast :one
SELECT a.id FROM authors a WHERE :guard::boolean;

-- name: not_guard :one
SELECT a.id FROM authors a WHERE NOT :not_guard;

-- name: or_guard :one
SELECT a.id FROM authors a WHERE :left_guard or :right_guard;

-- name: predicate :one
SELECT a.id FROM authors a WHERE :guard;
