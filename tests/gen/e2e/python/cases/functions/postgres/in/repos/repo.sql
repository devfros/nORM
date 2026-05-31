-- repo_name: Repo

-- name: CallFooText :one
SELECT app.foo(:bar::text);

-- name: CallFooInt :one
SELECT app.foo(:bar::integer);

-- name: CallAdd :one
SELECT app.add(:a, :b);

-- name: ListReturnsTable :many
SELECT id, name FROM app.returns_table(:x);
