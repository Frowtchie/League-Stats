# Changelog

## [Unreleased]
- (No changes yet)

## 0.3.0 - 2025-08-16
- Moved visualization TypedDict models from `stats_visualization/types.py` to `stats_visualization/viz_types.py` (prevents stdlib shadowing when running scripts inside package directory).
- Removed temporary shim `stats_visualization/types.py` (no external dependents).
- Documentation updated to recommend module invocation (`python -m stats_visualization.league`).

## 0.2.0 - 2025-08-15
- Added `save_figure` utility and migrated all visualization scripts to use it (consistent DPI, output dir handling).
- Introduced `sanitize_player` helper for safe filename construction (replaces manual `#` to `_`).
- Type hint refinements & centralized TypedDict models (`stats_visualization/viz_types.py`).
- Personal performance module refactored for consistency with shared utilities.

## 0.1.0 - Initial Public Draft
- Core fetch logic (`league.py`) with auto-fetch threshold.
- `analyze.py` unified CLI (Riot ID support, case-insensitive lookup, summary output, logging flags).
- Visualization suite (kills, drakes, barons/heralds, first blood, jungle clear, objectives, farming, personal performance).
- All visualizations save PNG outputs to `output/`.
- TypedDict-based lightweight data models.
- Documentation set: overview, architecture, CLI reference, metrics, visualization catalog, environment, fetching logic, player config, contributing, troubleshooting.
