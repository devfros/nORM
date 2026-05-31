-- repo_name: Repo

-- name: SelectAllJoinedAlias :many
select e.* from events e
    inner join handled_events he
       on e.ID > he.last_handled_id
where he.handler = :handler
    for update skip locked;

-- name: SelectAllJoined :many
select events.* from events
    inner join handled_events
       on events.ID > handled_events.last_handled_id
where handled_events.handler = :handler
    for update skip locked;
