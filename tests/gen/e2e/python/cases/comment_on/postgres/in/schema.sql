CREATE SCHEMA foo;

CREATE TYPE foo.mood AS ENUM ('sad', 'ok', 'happy');

CREATE TABLE foo.bar (
  baz foo.mood NOT NULL
);

COMMENT ON TYPE foo.mood IS 'this is the mood type';
COMMENT ON TABLE foo.bar IS 'this is the bar table';
COMMENT ON COLUMN foo.bar.baz IS 'this is the baz column';
