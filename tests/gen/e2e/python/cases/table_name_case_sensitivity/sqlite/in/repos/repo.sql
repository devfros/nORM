-- repo_name: Repo

-- name: InsertUser :exec
INSERT INTO users (name) VALUES (:name);

-- name: InsertUserMixedCase :exec
INSERT INTO users (name) VALUES (:name);

-- name: InsertAuthor :exec
INSERT INTO "Authors" (name) VALUES (:name);

-- name: InsertBook :exec
INSERT INTO Books (title) VALUES (:title);

-- name: UpdateUser :exec
UPDATE users SET name = :name WHERE id = :id;

-- name: UpdateUserMixedCase :exec
UPDATE users SET name = :name WHERE id = :id;

-- name: UpdateAuthor :exec
UPDATE "Authors" SET name = :name WHERE id = :id;

-- name: UpdateBook :exec
UPDATE Books SET title = :title WHERE id = :id;

-- name: DeleteUser :exec
DELETE FROM users WHERE id = :id;

-- name: DeleteUserMixedCase :exec
DELETE FROM users WHERE id = :id;

-- name: DeleteAuthor :exec
DELETE FROM "Authors" WHERE id = :id;

-- name: DeleteBook :exec
DELETE FROM Books WHERE id = :id;

-- name: GetUser :one
SELECT * FROM users WHERE id = :id;

-- name: GetUserMixedCase :one
SELECT * FROM users WHERE id = :id;

-- name: GetAuthor :one
SELECT * FROM "Authors" WHERE id = :id;

-- name: GetBook :one
SELECT * FROM Books WHERE id = :id;
