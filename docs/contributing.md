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
Follow the Release & Docs Policy:
1. Update affected docs (README, changelog, visualization catalog, CLI reference).
2. Move Unreleased entries to a dated version header in `docs/changelog.md`.
3. Bump `__version__` in `stats_visualization/__init__.py`.
4. Commit: `chore(release): vX.Y.Z`.
## Releasing
See the top-level `RELEASE_CHECKLIST.md`.

Minimum steps:
1. Update docs & changelog (move Unreleased).
2. Bump `__version__` in `stats_visualization/__init__.py`.
3. Commit with `chore(release): vX.Y.Z`.
4. Annotated tag & push (`git tag -a vX.Y.Z -m "League-Stats X.Y.Z"` then push code + tag).
5. (Optional) GitHub Release using changelog section.
