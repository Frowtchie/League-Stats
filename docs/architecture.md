# Architecture

## High-Level Flow
```
Riot API -> league.ensure_matches_for_player -> matches/*.json -> analysis (analyze.py & visualization scripts) -> output/*.png
```

## Core Modules
- `league.py`
  - `fetch_puuid_by_riot_id(game_name, tag_line, token)`
  - `fetch_match_ids(puuid, count)`
  - `fetch_match(match_id, token)` (includes timeline retrieval if available)
  - `ensure_matches_for_player(puuid, token, matches_dir, min_matches, fetch_count)`
  - Caching: Skips writing duplicates by existing JSON filename check.
- `analyze.py`
  - CLI: player/team analysis, auto-fetch logic, logging controls.
  - Player stats aggregation (K/D/A, win rate, roles, champions, gold, damage).
- Visualization scripts (`visualizations/*.py`)
  - Each loads matches via `analyze.load_match_files()` or bespoke helper.
  - Derive specialized metrics then produce and save matplotlib figures.

## Data Persistence
- Raw match JSON named `<MATCH_ID>.json` in `matches/`.
- Output charts saved as `output/<chart_type>_<player>.png`.
- Additional derived JSON (future) goes into `output/`.

## Error Handling
- Network/API errors caught and logged; fetch continues best-effort.
- Corrupt JSON skipped with warning.

## Case-Insensitive Riot ID Resolution
- `analyze.py` generates casing variants for game name and tag line until a successful PUUID fetch.

## Auto-Fetch Logic
1. Count local matches containing player PUUID.
2. If `< min_matches` and token present and not disabled, call `ensure_matches_for_player`.
3. Reload matches; summarize before/after counts.

## Extending
To add a new visualization:
1. Create a script in `visualizations/`.
2. Import `analyze.load_match_files` & `league` as needed.
3. Extract/derive metrics.
4. Save figure to `output/` with a descriptive filename.
5. Document in `visualizations_catalog.md` and CLI usage in `cli_reference.md`.
