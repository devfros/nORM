-- repo_name: Repo

-- name: GetAll :many
SELECT * FROM users;

-- name: NewUser :exec
INSERT INTO users (
    first_name,
    last_name,
    age,
    shoe_size,
    shirt_size
) VALUES
(
    :first_name,
    :last_name,
    :age,
    :shoe_size,
    :shirt_size
);

-- name: UpdateSizes :exec
UPDATE users
SET shoe_size = :shoe_size, shirt_size = :shirt_size
WHERE id = :id;

-- name: DeleteBySize :exec
DELETE FROM users
WHERE shoe_size = :shoe_size AND shirt_size = :shirt_size;
