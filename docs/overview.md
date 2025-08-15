# League-Stats Overview

Purpose: Fetch, store, analyze, and visualize personal League of Legends match data using the Riot API.

## Key Features
- Automatic match fetching with configurable minimums and batch sizes.
- Case-insensitive Riot ID and legacy player config support.
- Modular visualization scripts (objectives, drakes, barons/heralds, first blood, kills, farming, jungle clear, personal performance).
- Consistent output artifacts (PNG charts in `output/`, raw match JSON in `matches/`).
- Structured logging and auto-fetch logic in `analyze.py`.

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `config.env.example` to `config.env` and set `RIOT_API_TOKEN`.
3. (Optional) Add a player to config (legacy): update player mapping in code or use Riot ID directly.
4. Fetch + analyze:
   - `python stats_visualization/analyze.py --riot-id Frowtch blue --min-matches 10 --fetch-count 15`
5. Generate a visualization, e.g. drakes:
   - `python stats_visualization/visualizations/graph_drakes.py Frowtch blue`

## Directory Layout
- `stats_visualization/league.py` Riot API + data persistence helpers
- `stats_visualization/analyze.py` Core stats summary (player/team)
- `stats_visualization/visualizations/` Individual chart scripts
- `matches/` Cached raw match JSON
- `output/` Generated PNG charts / derived JSON
- `docs/` Project documentation

## Typical Workflow
Fetch or auto-fetch -> Inspect `analyze` report -> Run one or more visualization scripts -> Review saved PNGs in `output/`.

## Supported Python
Target: 3.12+ (currently using 3.13 locally).
