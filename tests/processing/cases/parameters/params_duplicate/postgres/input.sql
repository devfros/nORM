-- repo_name: TestRepo

-- name: SelectUserByID :many
SELECT first_name from
users where (:id = id OR :id = 0);

-- name: SelectUserByName :many
SELECT first_name
FROM users
WHERE first_name = :name
   OR last_name = :name;

-- name: SelectUserByAgeCast :many
SELECT first_name FROM users
WHERE age > CAST(:threshold AS INT)
   OR age < CAST(:threshold AS INT);
