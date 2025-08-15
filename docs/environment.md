# Environment & Configuration

## Required
- `RIOT_API_TOKEN`: Riot Developer API key (put in `config.env`).

## Loading
`.env` auto-loaded by visualization scripts via `dotenv` if `config.env` exists.

## Rate Limits
- Riot API short + long limits; excessive rapid fetches may cause 429 responses.
- Backoff strategy (future): simple sleep & retry.

## Directories
| Directory | Purpose |
|-----------|---------|
| `matches/` | Cached raw match JSON files |
| `output/` | Generated charts & derived datasets |

## Tokens & Security
- Never commit real `config.env`.
- Rotate tokens regularly; expired tokens produce 403/401 errors.

## Legacy Player Config
A local mapping (via `league.load_player_config()`) supports `--player` flag; Riot ID path preferred.

## System Requirements
- Python 3.12+ (tested 3.13)
- matplotlib, numpy, requests

## Optional Settings (Future)
- Proxy configuration for corporate networks
- Cache TTL for refreshing older matches
