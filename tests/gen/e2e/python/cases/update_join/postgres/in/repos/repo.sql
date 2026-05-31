-- repo_name: Repo

-- name: update_join :exec
UPDATE  join_table
SET     is_active = :is_active
FROM    primary_table
WHERE   join_table.id = :id
        AND primary_table.user_id = :user_id
        AND join_table.primary_table_id = primary_table.id;
