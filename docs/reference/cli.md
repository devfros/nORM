# CLI reference

```sh
norm [OPTIONS] COMMAND [ARGS]...
```

## Global options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to `norm.yaml` (default: `./norm.yaml` under `--cwd` or current directory) |
| `--cwd PATH` | Project root; paths resolve relative to this directory |
| `-v`, `--verbose` | Increase verbosity (repeat for more detail) |
| `-q`, `--quiet` | Suppress success and progress output |
| `--no-color` | Disable colored output (also respects `NO_COLOR`) |
| `--error-format` | `human` (default), `json`, or `github` |
| `--version` | Print package version |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Configuration, SQL, or code generation errors |
| `2` | Usage errors (invalid arguments, unimplemented migration commands) |

## Commands

| Command | Description |
|---------|-------------|
| `init` | Create `norm.yaml` and target directories |
| `targets` | List configured targets and paths |
| `generate` | Generate code from SQL sources |
| `check` | Verify generated output is up to date |
| `schema pull` | Pull Postgres schema via `pg_dump` |
| `migrations` | Placeholder (not implemented) |

## Shell completion

nORM uses Click shell completion when enabled in your shell environment.

- `--config` completes paths to `norm.yaml` files under `--cwd`
- `--target` / `-t` completes target names from `norm.yaml`

## Error formats

### Human (default)

Rich panels with an error code, message, optional source location, and hints.

### JSON

```sh
norm --error-format json check
```

Prints a single JSON object to stdout:

```json
{"code": "OUTOFDATE", "message": "...", "hint": "...", "context": {}}
```

### GitHub Actions

```sh
norm --error-format github check
```

Prints GitHub Actions workflow command annotations for CI.

## Typical workflow

```sh
norm init
norm schema pull --target default
norm generate
norm check
```
