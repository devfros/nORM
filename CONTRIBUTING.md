# Contributing to nORM

Thanks for your interest in nORM. This document covers local development and documentation.

## Repository

- **GitHub:** https://github.com/devfros/nORM
- **Docs site:** https://devfros.github.io/nORM

## Development setup

Requires Python **3.12+**.

```sh
git clone https://github.com/devfros/nORM.git
cd norm
poetry install --with dev
# or: pip install -e .
```

Run tests:

```sh
pytest
```

Lint:

```sh
ruff check .
```

The CLI entry point is `norm` (package name on PyPI: **`norm-cli`**).

## Documentation site

Docs live under `docs/` (VitePress).

```sh
cd docs
npm install
npm run docs:dev
```

Build for production:

```sh
npm run docs:build
```

Preview the production build:

```sh
npm run docs:preview
```

Edit pages under `docs/`; navigation is configured in `docs/.vitepress/config.ts`.

## Pull requests

1. Open an issue or discuss large changes first when unsure.
2. Keep PRs focused; match existing code style.
3. Update docs when behavior or CLI flags change.
4. Run `pytest` and `ruff check .` before submitting.

## Reporting issues

Use [GitHub Issues](https://github.com/devfros/nORM/issues) and include your `norm.yaml` (redact secrets), SQL snippets, and the `norm` command output when relevant.
