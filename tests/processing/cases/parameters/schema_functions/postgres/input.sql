-- repo_name: TestRepo

-- name: CallAdd :one
SELECT app.add(:a, :b);

-- name: CallFooText :one
SELECT app.foo(:bar::text);

-- name: CallFooInt :one
SELECT app.foo(:bar::integer);

-- name: CallFooAmbiguous :one
SELECT app.foo(:bar);

-- name: ListReturnsTable :many
SELECT id, name FROM app.returns_table(:x);
