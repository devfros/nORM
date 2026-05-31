CREATE TABLE users (id Int32, name String);

CREATE VIEW explicit_cols AS SELECT 1 AS x;
CREATE VIEW inferred_cols AS SELECT id, name FROM users;
