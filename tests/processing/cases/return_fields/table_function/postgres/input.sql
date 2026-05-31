-- repo_name: TestRepo

-- name: GetTransaction :many
SELECT
    jsonb_extract_path(transactions.data, '$.transaction.signatures[0]'),
    jsonb_agg(instructions.value)
FROM
  transactions,
    jsonb_each(jsonb_extract_path(transactions.data, '$.transaction.message.instructions[0]')) AS instructions
WHERE
    transactions.program_id = :program_id
    and jsonb_extract_path(transactions.data, '$.transaction.signatures[0]') @> to_jsonb(:data::text)
    and jsonb_extract_path(jsonb_extract_path(transactions.data, '$.transaction.message.accountKeys'), 'key') = to_jsonb(transactions.program_id)
GROUP BY transactions.id;
