# Changelog

## [Unreleased]
- (No changes yet)

## 0.2.0 - 2025-08-15
- Added `save_figure` utility and migrated all visualization scripts to use it (consistent DPI, output dir handling).
- Introduced `sanitize_player` helper for safe filename construction (replaces manual `#` to `_`).
- Type hint refinements & centralized TypedDict models (`stats_visualization/types.py`).
- Personal performance module refactored for consistency with shared utilities.

## 0.1.0 - Initial Public Draft
- Core fetch logic (`league.py`) with auto-fetch threshold.
- `analyze.py` unified CLI (Riot ID support, case-insensitive lookup, summary output, logging flags).
- Visualization suite (kills, drakes, barons/heralds, first blood, jungle clear, objectives, farming, personal performance).
- All visualizations save PNG outputs to `output/`.
- TypedDict-based lightweight data models.
- Documentation set: overview, architecture, CLI reference, metrics, visualization catalog, environment, fetching logic, player config, contributing, troubleshooting.
