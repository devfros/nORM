-- repo_name: TestRepo

-- name: CountAlertReportBy :many
select DATE_TRUNC(:date_trunc, ts)::text as datetime, coalesce(count, 0) as count from
(
    SELECT DATE_TRUNC(:date_trunc, eventdate) as hr, count(*)
    FROM alertreport
    where eventdate between :start_date and :end_date
    GROUP BY 1
) AS cnt
right outer join (SELECT * FROM generate_series(:start_date, :end_date, CONCAT('1 ', :date_trunc)::interval) AS ts) as dte
on DATE_TRUNC(:date_trunc, ts) = cnt.hr
order by 1 asc;
