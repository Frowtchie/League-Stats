# Troubleshooting

| Issue | Symptom | Fix |
|-------|---------|-----|
| Missing token | Message: RIOT_API_TOKEN not set | Add to `config.env` and retry |
| 401/403 errors | API calls fail immediately | Verify token validity & region |
| 429 rate limit | Fetch stops early | Wait, reduce `--fetch-count` |
| No matches found | Zero games after fetch | Increase `--fetch-count`, verify PUUID |
| Wrong player data | Stats zero or mismatched | Check Riot ID casing; verify region (Americas routing assumed) |
| Charts empty | PNG shows placeholders/no bars | Ensure enough games for that metric (e.g., role min 2 games) |
| Unicode in filenames | Saved file missing | `#` replaced with `_`, ensure filesystem supports name |
| Slow plotting | Large dataset lag | Limit matches or pre-filter; use Agg backend headless |

## Debugging Tips
- Use `--debug` to enable verbose logs in `analyze.py`.
- Manually inspect a match file in `matches/` to confirm participant PUUID.
- Cross-check PUUID via direct Riot API call if suspicion of mismatch.

## Common Data Gaps
- Some timelines unavailable (older or special modes).
- Incomplete objective fields in non-SR modes; scripts skip gracefully.

## Regenerating Outputs
Delete specific PNG in `output/` and re-run the corresponding visualization script.
