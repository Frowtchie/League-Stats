# CLI Cheat Sheet

Ultra‑compact reference for frequent commands and flags. See `cli_reference.md` for full detail.

## Core Commands
```
# Fetch matches (module form recommended)
python -m stats_visualization.league <IGN> <TAG> <COUNT>

# Fetch with async mode (default) with custom concurrency
python -m stats_visualization.league <IGN> <TAG> <COUNT> --concurrency 12

# Analyze (Riot ID preferred)
python analyze.py -i <IGN> <TAG> [flags]

# Generate all visuals after analysis
python analyze.py -i <IGN> <TAG> -g

# Individual visualization (examples)
python stats_visualization/visualizations/personal_performance.py <IGN> <TAG> -c all
python stats_visualization/visualizations/objective_analysis.py <IGN> <TAG> -c control
python stats_visualization/visualizations/farming_analysis.py <IGN> <TAG> -c roles
```

## High‑Frequency Flags (Short / Long)
| Analyze / Visualizations | Purpose |
|--------------------------|---------|
| `-i / --riot-id` GAME TAG | Specify Riot ID (preferred) |
| `-p / --player` NAME | Legacy configured player name |
| `-m / --matches-dir DIR` | Match JSON directory (default `matches`) |
| `-g / --generate-visuals` | After analysis, build all charts |
| `-a / --include-aram` | Include ARAM (excluded by default) |
| `-q / --queue IDS` | Restrict to queue IDs (e.g. `420 440`) |
| `-R / --ranked-only` | Shortcut for solo+flex (`420 440`) |
| `-M / --modes MODES` | Whitelist gameMode values (e.g. `CLASSIC`) |
| `-O / --no-clean-output` | Keep existing PNGs (skip auto cleanup) |

### Analyze‑Only Extras
| Flag | Purpose |
|------|---------|
| `-t / --team-analysis` | Team/objective aggregate view |
| `-n / --min-matches N` | Auto‑fetch threshold (default 5) |
| `-f / --fetch-count N` | Matches to fetch when needed (default 10) |
| `-X / --no-auto-fetch` | Disable auto fetch |
| `-d / --debug` | Force DEBUG logging |
| `-l / --log-level LEVEL` | Set log level (INFO default) |

### Match Fetching (league.py) Extras
| Flag | Purpose |
|------|---------|
| `--sync-mode` | Force synchronous mode (async is default) |
| `--concurrency N` | Max concurrent requests (default 8) |
| `--metrics-json FILE` | Export fetch metrics to JSON |
| `--no-cache` | Disable caching, re-fetch all |

### Visualization Script Extras
| Script | Flag (short/long) | Purpose |
|--------|-------------------|---------|
| personal_performance | `-c / --chart` | trends, champions, roles, all |
| farming_analysis | `-c / --chart` | farming, gold, roles, all |
| objective_analysis | `-c / --chart` | control, first, correlation, all |
| graph_kills | `-D / --detailed` | Champion breakdown |
| graph_first_bloods | `-r / --role-comparison` | Role early game comparison |

## Common One‑Liners
```
# Ranked only analysis + visuals
python analyze.py -i Frowtch blue -R -g

# Analyze with ARAM & specific modes
python analyze.py -i Frowtch blue -a -M CLASSIC CHERRY

# Objective control (ranked only)
python stats_visualization/visualizations/objective_analysis.py Frowtch blue -c control -R

# Personal performance (champions only, keep old PNGs)
python stats_visualization/visualizations/personal_performance.py Frowtch blue -c champions -O

# Farming roles view for Solo Queue only
python stats_visualization/visualizations/farming_analysis.py Frowtch blue -c roles -q 420
```

## Filtering Logic Summary
- ARAM excluded unless `-a` / `--include-aram`.
- If queues provided (`-q`) match must have queueId in list.
- `-R` sets queue filter to 420 & 440 if none provided.
- If modes provided (`-M`), match `gameMode` must be in the set (combined with other filters by AND).

## Output Behavior
- Visualization scripts clean `output/*.png` unless `-O`.
- `-g` in `analyze.py` runs full visualization suite (same cleaning unless `-O`).

## Minimal Troubleshooting
| Symptom | Quick Fix |
|---------|-----------|
| "RIOT_API_TOKEN not set" | Add token to `config.env` (no manual export needed) |
| No matches found | Fetch: `python -m stats_visualization.league <GAME> <TAG> 10` |
| Charts missing | Remove `-O` (ensure cleanup) or verify `output/` write perms |
| Filters yield 0 games | Relax `-q`/`-M` or drop `-R`/`-a` interplay |

## Match Fetch Queues (Common IDs)
| ID | Queue |
|----|-------|
| 420 | Ranked Solo/Duo |
| 440 | Ranked Flex |
| 430 | Normal Draft |
| 400 | Normal Blind |
| 450 | ARAM |

---
For complete descriptions see `docs/cli_reference.md`.
