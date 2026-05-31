-- repo_name: Repo

-- name: InsertContact :exec
INSERT INTO contacts (
    pid,
    CustomerName
)
VALUES (:pid, :CustomerName);
