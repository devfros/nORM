-- repo_name: TestRepo

-- name: ListTasks :many
SELECT * FROM tasks;

-- name: GetTasksByStatus :many
SELECT * FROM tasks WHERE status = :status;

-- name: CreateTask :one
INSERT INTO tasks (title, status) VALUES (:title, :status) RETURNING *;
