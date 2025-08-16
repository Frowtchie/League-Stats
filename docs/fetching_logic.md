# Fetching Logic & Auto-Fetch

## Goal
Ensure a minimum number of recent matches locally for analysis without manual intervention.

## Core Function
`league.ensure_matches_for_player(puuid, token, matches_dir, min_matches, fetch_count)`:
1. Count existing local matches for the player.
2. If below `min_matches`, request up to `fetch_count` new match IDs.
3. For each new ID not already present, fetch full match (and timeline if available) and save JSON.
4. Return updated count.

## analyze.py Integration
- Flags: `--min-matches`, `--fetch-count`, `--no-auto-fetch`.
- After player PUUID resolution, counts player matches and optionally triggers fetch.
- Prints summary: before -> after counts and time taken.

## Case-Insensitive Riot ID Resolution
- Generates variants (original, lower, upper, title) for the IGN (in‑game name) & tag line.
- Attempts each until PUUID fetch succeeds or exhausts variants.

## Failure Modes
| Scenario | Behavior |
|----------|----------|
| Missing token | Skip fetch, advise user |
| Network/API error | Log warning, continue remaining IDs |
| No new matches | Summary notes zero delta |

## Best Practices
- Keep `fetch_count` modest (10-20) to reduce rate limit pressure.
- Increase `min_matches` when doing longitudinal analysis.
- Periodically prune stale match files if disk usage grows.

## Future Enhancements
- Parallel fetch with rate limit pacing.
- Incremental update (only newest N matches).
- Cache metadata index for faster player match counting.
