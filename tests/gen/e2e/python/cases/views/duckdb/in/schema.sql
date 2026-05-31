CREATE TABLE users (id int, name text);

CREATE VIEW explicit_cols(x) AS SELECT 1 AS x;
CREATE VIEW inferred_cols AS SELECT id, name FROM users;
