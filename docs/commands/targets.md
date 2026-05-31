# `targets` - list configured targets

Show target names and resolved paths without connecting to a database or generating code.

## Usage

```sh
norm targets
norm targets --target default
```

## Options

- `--target`, `-t`: Show only the named target.

## Output

A table with:

- Target name
- SQL engine
- Schema file path
- Repositories directory
- Generated output directory

Paths are shown relative to the project root (`--cwd` or the directory containing `norm.yaml`).
