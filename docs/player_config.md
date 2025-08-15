# Player Configuration (Legacy Mode)

## Overview
Legacy `--player` flag loads a local mapping of friendly names -> PUUIDs via `league.load_player_config()`.

## Why Keep It?
- Backwards compatibility.
- Offline reuse without repeated Riot ID lookups.

## Recommended Migration
Prefer `--riot-id GAME TAG` which performs live PUUID lookup (with case-insensitive attempts).

## Adding a Player
Update the player config source (e.g., JSON or dict inside `league.py` if currently hard-coded) with the new mapping.

## Case Insensitivity
`analyze.py` normalizes `--player` by lowercasing and matching against a lowercase -> canonical map.

## Removal Plan (Future)
- Deprecation warning when `--player` used.
- Provide export/import tool for mapping if externalized.
