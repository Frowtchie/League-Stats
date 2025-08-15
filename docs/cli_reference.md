# CLI Reference

## Common Pattern
```
python stats_visualization/analyze.py --riot-id <GAME_NAME> <TAG_LINE> [options]
python stats_visualization/visualizations/<script>.py <GAME_NAME> <TAG_LINE> [options]
```

All PNG outputs land in `output/`.

## analyze.py
| Flag | Description | Default |
|------|-------------|---------|
| `--riot-id GAME TAG` | Use Riot ID (preferred) | - |
| `--player NAME` | Legacy config lookup (case-insensitive) | - |
| `--team-analysis` | Aggregate team/objective stats | off |
| `--matches-dir DIR` | Match JSON directory | `matches` |
| `--debug` | Force DEBUG logging | off |
| `--log-level LEVEL` | Logging level (CRITICAL..DEBUG) | INFO |
| `--min-matches N` | Minimum player matches required (auto-fetch trigger) | 5 |
| `--fetch-count N` | Matches to fetch when auto-fetching | 10 |
| `--no-auto-fetch` | Disable auto-fetch | off |

Examples:
```
python stats_visualization/analyze.py --riot-id Frowtch blue --min-matches 12 --fetch-count 20
python stats_visualization/analyze.py --player frowtch --team-analysis
```

## Visualization Scripts
All visualization scripts accept `GAME_NAME TAG_LINE` and `--matches-dir`.

| Script | Purpose | Extra Flags |
|--------|---------|-------------|
| `visualizations/graph_drakes.py` | Personal drake & dragon control trends | - |
| `visualizations/graph_barons_heralds.py` | Baron & Herald control comparison | - |
| `visualizations/graph_first_bloods.py` | Early game & first blood stats | `--role-comparison` |
| `visualizations/graph_kills.py` | Kills, assists, KDA progression | - |
| `visualizations/farming_analysis.py` | CS/min, gold efficiency, role economy | `--chart farming|gold|roles|all` |
| `visualizations/jungle_clear_analysis.py` | Jungle first clear timing, efficiency | - |
| `visualizations/objective_analysis.py` | Objective control & first objectives | (planned options) |
| `visualizations/personal_performance.py` | Trends, champions, role performance | `--chart trends|champions|roles|all` |

## Output Filenames
Pattern: `<topic>_<PLAYER>.png` (Riot ID `#` replaced by `_`).

## Exit Conditions
- Missing token prints message & exits.
- Unknown player (legacy) prints available list & exits.
- No matches after fetch prints advisory.

## Logging
`--debug` overrides `--log-level`. Auto-fetch summary always prints a success line on completion.
