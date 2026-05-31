CREATE TABLE authors (
  id          BIGINT PRIMARY KEY,
  foo         ENUM("ok") DEFAULT "ok" NOT NULL,
  renamed     ENUM("ok") DEFAULT "ok" NOT NULL,
  removed     ENUM("ok") DEFAULT "ok" NOT NULL,
  add_item    ENUM("ok") DEFAULT "ok" NOT NULL,
  remove_item ENUM("ok", "removed") DEFAULT "ok" NOT NULL
);
