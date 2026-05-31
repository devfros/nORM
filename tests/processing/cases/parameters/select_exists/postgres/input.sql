-- repo_name: TestRepo

-- name: BarExists :one
SELECT
    EXISTS (
        SELECT 1
        FROM bar
        where id = :id
    );
