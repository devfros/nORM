-- repo_name: TestRepo

-- name: current_date :one
SELECT * FROM books WHERE available > CURRENT_DATE;

-- name: current_timestamp :one
SELECT * FROM books WHERE available > CURRENT_TIMESTAMP;
