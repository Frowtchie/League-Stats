
# Changelog
## Unreleased
- Added [glossary](glossary.md) with definitions for IGN, Riot ID, PUUID, Queue ID, Game Mode, Role, Timeline, Objective.
- Updated [architecture diagram](architecture.svg) to include filtering logic and async branch placeholder.
- Cross-linked glossary terms in README and CLI reference for onboarding clarity.

## 1.0.0 - 2025-08-17
- First stable release. Introduces Streamlit GUI prototype (`stats_visualization/gui_app.py`) for interactive chart generation, filtering (ranked only, ARAM inclusion, queue & mode filters), and modal image gallery with download.
- Adds MkDocs documentation site structure (`docs/` with architecture, metrics, visualization catalog, CLI reference, troubleshooting, etc.) and configuration (`mkdocs.yml`).
- Centralized filtering across CLI and visualization scripts (queue IDs, ranked-only shortcut, game mode whitelist, ARAM toggle).
- Bulk visualization generation workflow exposed via GUI using existing `analyze.generate_all_visuals` logic.
- General polish: lint compliance, version synchronization, robust import handling, output directory hygiene improvements.

## 0.5.0 - 2025-08-17
- Modernized project structure: added `pyproject.toml` for PEP 621/517/518 compliance and tool configuration.
- Version synchronization: all version numbers (`pyproject.toml`, `__init__.py`, and docstrings) are now kept in sync and updated together for each release.
- Improved `.gitignore`: added `logs/` and other generated folders to prevent accidental commits of large or sensitive files.
- Changelog and release workflow: clarified and automated changelog and version bumping for future releases.
- General code and documentation cleanup: fixed indentation, removed stray code, and improved docstring placement for clarity and maintainability.

## 0.4.0 - 2025-08-16
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
