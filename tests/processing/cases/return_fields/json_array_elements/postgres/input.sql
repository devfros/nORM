-- repo_name: TestRepo

-- name: GetActionCodeByResource :one
SELECT code, arr.item_object ->> 'code'  as resource_code
FROM sys_actions,
    jsonb_array_elements(resources) with ordinality arr(item_object, resource)
    WHERE item_object->>'resource' = :resource
    LIMIT 1;
