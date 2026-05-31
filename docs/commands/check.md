# `check` - check generated code sync

Check whether generated code is up to date with the configured SQL sources.

## Usage

```sh
norm check
norm check --target default
norm check -t default
norm check --diff
norm check --fix
norm check --strict
```

## Options

- `--target`, `-t`: Limit the check to a specific target.
- `--diff`: Show a unified diff for each stale file.
- `--fix`: Regenerate targets that are out of date. This is equivalent to running `norm generate` for those targets.
- `--strict`: Exit with an error when no generated files exist to compare.

## Behavior

- Runs generation logic for the selected target(s).
- Compares generated output with existing files in `gen.out`.
- Prints stale file paths when output is out of date.
- Exits with code `1` when output is stale, or when `--strict` finds nothing to compare.

## Common errors

- Unknown target name in `--target`.
- `OUTOFDATE` when generated files differ from current SQL (run `norm generate` or `norm check --fix`).
