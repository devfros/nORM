# `generate` - generate code

Generate code from configured schema and repository SQL files.

## Usage

```sh
norm generate
norm generate --target default
norm generate -t default
norm generate --parallel
```

## Options

- `--target`, `-t`: Generate for a specific target defined in `norm.yaml`.
- `--parallel`: When multiple targets are configured, generate them in parallel with up to four worker processes. Without this flag, targets run sequentially.

## Behavior

- Without `--target`, nORM generates code for all targets in `norm.yaml`.
- With `--target`, nORM generates only that target.
- The command parses:
  - `sql.db_schema`
  - all `*.sql` files inside `sql.repositories`
- Before writing output, nORM removes and recreates the target's existing `gen.out` directory.
- Prints a success summary per target (file count and duration) unless `--quiet` is set.

## Common errors

- Unknown target name in `--target`.
- Missing or invalid schema file.
- No repository SQL files found in `sql.repositories`.
- SQL parse errors in repository files.
