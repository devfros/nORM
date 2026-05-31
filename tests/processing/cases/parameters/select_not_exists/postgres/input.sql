-- repo_name: TestRepo

-- name: BarNotExists :one
SELECT
    NOT EXISTS (
        SELECT 1
        FROM bar
        where id = :id
    );
