# Contributing

## Workflow
1. Fork & clone.
2. Create a feature branch: `feat/<slug>`.
3. Add / modify code & tests.
4. Run local checks (see below).
5. Open PR with concise description & screenshots of new charts.

## Local Checks
- Lint/type (optional): `python -m py_compile $(git ls-files '*.py')` or run mypy if configured.
- Run tests: `pytest -q`.

## Code Style
- Prefer explicit imports.
- Keep functions < ~60 lines; extract helpers.
- Reuse the shared figure save helper (see `stats_visualization/__init__.py`).

## Adding a Visualization
1. Place module in `stats_visualization/visualizations/`.
2. Provide a `generate_<topic>_charts(data, output_dir)` entry.
3. Save each figure via `save_figure(fig, output_dir, slug)`.
4. Append an entry to `docs/visualizations_catalog.md`.
5. Add a minimal test (see existing tests as template).

## Commit Messages
Conventional prefix recommended:
- feat: new capability
- fix: bug fix
- docs: docs only
- refactor: no behavior change
- test: tests only
- chore: tooling/infra

## Versioning
Semantic-ish; increment minor for features, patch for fixes.

## Releasing
Update `CHANGELOG.md` (Unreleased -> date) then tag: `git tag vX.Y.Z`.
