# CLI Reference

> See the [Glossary](glossary.md) for definitions of IGN, Riot ID, Queue ID, Game Mode, Role, and other terms used below.

## Common Pattern
```
python stats_visualization/analyze.py --riot-id <IGN> <TAG_LINE> [options]
python stats_visualization/visualizations/<script>.py <IGN> <TAG_LINE> [options]
```

All PNG outputs land in `output/`.

## analyze.py
Short aliases have been added; long forms still work. Examples: `-i`, `-p`, `-m`, `-g`, `-a`, `-q`, `-R`, `-M`, `-O`.

| Short | Long | Description | Default |
|-------|------|-------------|---------|
| `-i` | `--riot-id IGN TAG` | Use Riot ID (preferred; [IGN](glossary.md#ign) = in-game name) | - |
| `-p` | `--player NAME` | Legacy config lookup (case-insensitive) | - |
| (none) | `--team-analysis` | Aggregate team/objective stats | off |
| `-m` | `--matches-dir DIR` | Match JSON directory | `matches` |
| (none) | `--debug` | Force DEBUG logging | off |
| (none) | `--log-level LEVEL` | Logging level (CRITICAL..DEBUG) | INFO |
| (none) | `--min-matches N` | Minimum player matches required (auto-fetch trigger) | 5 |
| (none) | `--fetch-count N` | Matches to fetch when auto-fetching | 10 |
| (none) | `--no-auto-fetch` | Disable auto-fetch | off |
| `-a` | `--include-aram` | Include ARAM (excluded by default) | off |
| `-q` | `--queue IDS` | Whitelist [queue IDs](glossary.md#queue-id) (e.g. `420 440`) | all |
| `-R` | `--ranked-only` | Shortcut for `--queue 420 440` | off |
| `-M` | `--modes MODES` | Whitelist [gameMode](glossary.md#game-mode) values (e.g. `CLASSIC`) | all |
| `-g` | `--generate-visuals` | After analysis generate all charts | off |
| `-O` | `--no-clean-output` | With --generate-visuals, keep existing PNGs | off |

Examples (short + long forms mixed):
```
python stats_visualization/analyze.py -i Frowtch blue --min-matches 12 --fetch-count 20
python stats_visualization/analyze.py -i Frowtch blue -R
python stats_visualization/analyze.py -i Frowtch blue -q 420 440 -M CLASSIC
python stats_visualization/analyze.py -p frowtch --team-analysis -q 420
python stats_visualization/analyze.py -i Frowtch blue -g -O
```

Filtering behavior matches visualization scripts: ARAM excluded unless `--include-aram` set; if any of `--queue` / `--modes` specified a match must satisfy all provided criteria.

## Visualization Scripts
All visualization scripts accept `IGN TAG_LINE` plus filtering flags. Short aliases mirror analyze.py (`-m`, `-a`, `-q`, `-R`, `-M`, `-O`).

| Script | Purpose | Extra Flags (short aliases) |
|--------|---------|----------------------------|
| `visualizations/graph_drakes.py` | Personal drake & dragon control trends | Filtering flags* |
| `visualizations/graph_barons_heralds.py` | Baron & Herald control comparison | Filtering flags* |
| `visualizations/graph_first_bloods.py` | Early game & first blood stats | `-r/--role-comparison` + [Role](glossary.md#role) filtering flags* |
| `visualizations/graph_kills.py` | Kills, assists, KDA progression | Filtering flags* |
| `visualizations/farming_analysis.py` | CS/min, gold efficiency, role economy | `-c/--chart farming|gold|roles|all` + Filtering flags* |
| `visualizations/jungle_clear_analysis.py` | Jungle first clear timing, efficiency | Filtering flags* |
| `visualizations/lane_cs_diff.py` | Lane phase lane metrics (CS) + separate XP/Gold diff timeline | Filtering flags* |
| `visualizations/objective_analysis.py` | Objective control & first objectives | `-c/--chart control|first|correlation|all` + Filtering flags* |
| `visualizations/personal_performance.py` | Trends, champions, role performance | `-c/--chart trends|champions|roles|all` + Filtering flags* |

## Output Filenames
Pattern: `<topic>_<PLAYER>.png` (Riot ID `#` replaced by `_`). ARAM matches are excluded by default for scripts using central filtering unless `--include-aram` is passed.

### Output Cleaning

By default, running any visualization script now clears existing `output/*.png` files before generating new charts. Use `--no-clean-output` to preserve previous images.

### *Filtering Flags (centralized)

| Short | Long | Purpose | Notes |
|-------|------|---------|-------|
| `-a` | `--include-aram` | Include ARAM games | Default: exclude ARAM |
| `-q` | `--queue QIDS` | Whitelist queue IDs | e.g. `-q 420 440` |
| `-R` | `--ranked-only` | Shortcut for `--queue 420 440` | Solo + Flex ranked |
| `-M` | `--modes MODES` | Whitelist gameMode values | e.g. `-M CLASSIC URF` |
| `-O` | `--no-clean-output` | Keep existing PNGs | Default: delete before run |

If multiple filters are provided, a match must satisfy all of them to be included.

## Exit Conditions
- Missing token prints message & exits.
- Unknown player (legacy) prints available list & exits.
- No matches after fetch prints advisory.

## Logging
`--debug` overrides `--log-level`. Auto-fetch summary always prints a success line on completion.

## league.py (Data Fetching)
Direct match data fetching from Riot API. Requires `RIOT_API_TOKEN` environment variable.

Usage: `python stats_visualization/league.py <IGN> <TAG_LINE> <COUNT> [options]`

| Option | Description | Default |
|--------|-------------|---------|
| `--log-level LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `--no-cache` | Disable caching and re-fetch all matches | off |
| `--sync-mode` | Use synchronous mode instead of default async/batched fetching | off |
| `--concurrency N` | Maximum concurrent requests when using async mode | 8 |
| `--metrics-json FILE` | Export metrics to JSON file | - |

### Default Async Mode Benefits
- Significantly faster when fetching multiple matches (default behavior)
- Utilizes network concurrency with rate limit respect  
- Provides detailed performance metrics
- Graceful fallback to sync mode if httpx unavailable

Example:
```bash
# Async mode with default concurrency (default behavior)
python stats_visualization/league.py Frowtch blue 10

# Async mode with custom concurrency and metrics export
python stats_visualization/league.py Frowtch blue 20 --concurrency 12 --metrics-json metrics.json

# Force sync mode for compatibility
python stats_visualization/league.py Frowtch blue 10 --sync-mode
```
