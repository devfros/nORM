CREATE TABLE authors (
    id Int32,
    name String DEFAULT '',
    rating Nullable(Int32)
)
ENGINE = MergeTree()
ORDER BY id;

CREATE TABLE books (
    id Int32,
    author_id Int32,
    isbn String DEFAULT '',
    book_type String DEFAULT 'FICTION',
    title String DEFAULT '',
    year Int32 DEFAULT 2000,
    available DateTime64(6, 'UTC') DEFAULT now64(),
    tags Array(String)
)
ENGINE = MergeTree()
ORDER BY id;
