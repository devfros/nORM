# `init` - initialize a project

Create `norm.yaml` and the input directory layout for configured targets.

## Usage

```sh
norm init
norm init --dry-run
norm init --force
```

## Options

- `--dry-run`: Print paths that would be created without writing files.
- `--force`: Create missing paths only. Existing `norm.yaml` files are not overwritten.

## Behavior

- Creates `norm.yaml` from the default template when missing.
- Creates `sql.repositories`, schema parent directories, and an empty schema file for each target.
- If the project is already initialized, prints `Already initialized` and exits successfully.
