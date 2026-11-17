# Contributing

Thank you for helping improve the Routune Python library.

## Development

```sh
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m mypy
python -m pytest
```

## Generated code

`src/routune/types/_models.py` and `src/routune/types/_params.py` are generated from `openapi/routune-public.v1.json`. Do not edit them by hand. To update them after an API change:

```sh
python scripts/generate.py
```

CI fails when the generated files are out of date (`python scripts/generate.py --check`).

## Pull requests

- Keep changes focused and include tests for new behaviour.
- Describe user-facing changes in `CHANGELOG.md`.
- For larger changes, open an issue first so we can agree on the approach.
