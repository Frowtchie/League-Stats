# Environment & Configuration

## Required
- `RIOT_API_TOKEN`: Riot Developer API key (put in `config.env`).

## Loading
`config.env` is auto-loaded by all scripts (league, analyze, visualizations) via `python-dotenv` when present.

## Rate Limits
- Riot API short + long limits; excessive rapid fetches may cause 429 responses.
- Backoff strategy (future): simple sleep & retry.

## Directories
| Directory | Purpose |
|-----------|---------|
| `matches/` | Cached raw match JSON files |
| `output/` | Generated charts & derived datasets |
| `logs/` | Application logs (`league_stats.log`) from CLI, Analyze, and GUI |

## Tokens & Security
- Never commit real `config.env`.
- Rotate tokens regularly; expired tokens produce 403/401 errors.

## Legacy Player Config
A local mapping (via `league.load_player_config()`) supports `--player` flag; Riot ID path preferred.

## System Requirements
- Python 3.12+ (tested 3.13)
- matplotlib, numpy, requests
 - Optional: `httpx` (enables async fetching in the CLI; without it the CLI falls back to sync automatically)

## Logging
- All entrypoints initialize persistent file logging via `utils.setup_file_logging()`.
- Log file: `logs/league_stats.log`.
- The Streamlit GUI records key steps (PUUID resolution, ensuring matches, visualization generation, completion/errors).

## Optional Settings (Future)
- Proxy configuration for corporate networks
- Cache TTL for refreshing older matches
