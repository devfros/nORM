CREATE TABLE authors (
    id          Int64,
    foo         Enum8('ok' = 1),
    renamed     Enum8('ok' = 1),
    removed     Enum8('ok' = 1),
    add_item    Enum8('ok' = 1),
    remove_item Enum8('ok' = 1, 'removed' = 2)
) ENGINE = MergeTree()
ORDER BY id;
