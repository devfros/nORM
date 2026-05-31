-- repo_name: TestRepo

-- name: GetGroups :many
SELECT
    rg.groupId,
    rg.groupName
FROM
    RouterGroup rg
WHERE
    rg.groupName LIKE CONCAT('%', COALESCE(n.narg(:groupName)::text, rg.groupName), '%') AND
    rg.groupId = COALESCE(n.narg(:groupId), rg.groupId);
