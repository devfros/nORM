-- repo_name: TestRepo

-- name: Test2 :one
select * from Demo
where txt like '%' || :val::text || '%';

-- name: Test3 :one
select * from Demo
where txt like concat('%', :val::text, '%');
