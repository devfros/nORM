-- repo_name: Repo

-- name: GetTotalSlackQueries :one
SELECT
    COUNT(*) AS count
FROM astoria.slack_feedback
WHERE astoria.slack_feedback.workspace_id = :workspace_id
AND created_at BETWEEN :start::date AND :end::date;

-- name: GetTotalSlackQueriesResolved :one
SELECT
    COUNT(*) AS count
FROM astoria.slack_feedback
WHERE astoria.slack_feedback.workspace_id = :workspace_id
  AND (issue_raised = false OR issue_raised IS NULL)
AND created_at BETWEEN :start::date AND :end::date;

-- name: GetTotalSlackQueriesRequestsCreated :one
SELECT
    COUNT(*) AS count
FROM astoria.tickets
WHERE astoria.tickets.workspace_id = :workspace_id
  AND source = 'RAISED_FROM_BOT'
AND created_at BETWEEN :start::date AND :end::date;
