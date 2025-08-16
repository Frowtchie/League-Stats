# Changelog

## [Unreleased]
### Planned for 0.5.0 (Draft)
- Performance: Optional async/batched Riot API fetches; lightweight caching metrics.
- Data Quality: Validation report for missing timeline segments & selective refetch.
- New Visualizations: Role impact (gold/xp share), damage composition, lane phase CS diff, objective participation heatmap.
- Configuration: Central `player_config.yml` supporting multiple profiles + aliases.
- CLI UX: Progress bars for fetch, colored summaries, `--json` output option.
- Packaging: PyPI-ready (`pyproject.toml`), console scripts entry points.
- Extensibility: Plugin discovery via entry points for custom visualizations.
- CI: GitHub Actions workflow (lint, tests, mypy, coverage badge).
- Docs: Add glossary (IGN, Riot ID, PUUID, Queue ID) & updated architecture diagram.
- Reliability: Smarter rate limit backoff with jitter & structured log events.

## 0.4.0 - 2025-08-16
### Added
- Centralized match filtering (ARAM exclusion by default, `--include-aram`, `--queue`, `--ranked-only`, `--modes`) extended to `analyze.py` (parity with visualization scripts).
- `analyze.py` flag `--generate-visuals` to produce the full visualization suite post textual analysis (with `--no-clean-output` opt-out of initial cleanup).
- Short flag aliases across CLI (`-i/-p/-t/-m/-d/-l/-n/-f/-X/-a/-q/-R/-M/-g/-O`, plus visualization script equivalents like `-c`, `-D`, `-r`) for faster interactive use.

### Documentation
- Updated README and CLI reference to include new `analyze.py` filtering flags and examples.
- Added condensed `cli_cheatsheet.md` for quick flag and command reference.
- Replaced ambiguous term 'game name' with 'IGN (in-game name)' across CLI help, docs, and examples for clarity.

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
