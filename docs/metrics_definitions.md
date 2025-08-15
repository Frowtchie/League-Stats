# Metrics Definitions

| Metric | Formula / Source | Notes |
|--------|------------------|-------|
| Win Rate | wins / total_games | Displayed as percentage in reports. |
| KDA | (kills + assists) / max(1, deaths) | Avoid divide-by-zero. |
| CS per Minute | (lane minions + neutral minions) / (gameDuration/60) | Skips invalid durations. |
| Gold per Minute | goldEarned / (gameDuration/60) | Rounded for display. |
| Damage per Gold | totalDamageDealtToChampions / goldEarned | 0 if goldEarned == 0. |
| Vision Score | participant.visionScore | Raw from match data. |
| Clear Efficiency | neutralMinionsKilled / (gameDuration/60) | Jungle early efficiency proxy. |
| First Clear Time (est.) | Timeline-based or heuristic (see below) | Jungle clear estimation. |
| Kill Participation | (kills + assists) / teamKills * 100 | Team kills aggregated by teamId. |
| Objective Advantage | player_team_objectives - enemy_team_objectives | Per match; aggregated. |
| Early Game K/D Proxy | early_kills / max(1, early_deaths) | Used in first blood script for grouping. |

## Jungle First Clear Heuristic
1. If timeline frames present: derive from jungle camp kill events timestamps.
2. Else approximate using neutral CS thresholds and champion baseline times.

## First Objective Success Rates
Counts of `first` flags in team objectives for dragon, baron, herald, tower divided by total games.

## Data Quality Handling
- Missing numeric fields treated as 0.
- Corrupt or incomplete match JSON skipped.
- Average durations computed only over counted matches.

## Future Metrics (Roadmap)
- Gold Diff @ 10/15 (needs timeline or frame deltas)
- CS Diff @ 10
- Objective Bounties Impact
- Damage Share & Gold Share
- Vision Efficiency (wards per minute x clear attempts)
