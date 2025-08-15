#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data analysis module for League of Legends match data.
Provides basic statistics and insights from saved match data.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
import logging

# Allow running as a script (python stats_visualization/analyze.py) by adding project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT)) if str(PROJECT_ROOT) not in sys.path else None

logger = logging.getLogger(__name__)


def _count_player_matches(matches: List[Dict[str, Any]], player_puuid: str) -> int:
    """Return number of matches in which the player participated."""
    count = 0
    for m in matches:
        info = m.get("info", {})
        for p in info.get("participants", []):
            if p.get("puuid") == player_puuid:
                count += 1
                break
    return count


def load_match_files(matches_dir: str = "matches") -> List[Dict[str, Any]]:
    """
    Load all match data files from the matches directory.

    Args:
        matches_dir (str): Directory containing match JSON files

    Returns:
        List[Dict]: List of match data dictionaries
    """
    matches = []
    matches_path = Path(matches_dir)

    if not matches_path.exists():
        logger.warning(f"Matches directory {matches_dir} does not exist")
        return matches

    for file_path in matches_path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                match_data = json.load(f)
                matches.append(match_data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load {file_path}: {e}")

    logger.info(f"Loaded {len(matches)} match files")
    return matches


def analyze_player_performance(
    matches: List[Dict[str, Any]], player_puuid: str
) -> Dict[str, Any]:
    """
    Analyze performance statistics for a specific player.

    Args:
        matches (List[Dict]): List of match data
        player_puuid (str): PUUID of the player to analyze

    Returns:
        Dict[str, Any]: Performance statistics
    """
    stats = {
        "total_games": 0,
        "wins": 0,
        "losses": 0,
        "total_kills": 0,
        "total_deaths": 0,
        "total_assists": 0,
        "champions_played": Counter(),
        "roles_played": Counter(),
        "average_game_duration": 0,
        "total_damage": 0,
        "total_gold": 0,
    }

    total_duration = 0

    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue

        # Find the player's data in this match
        player_data = None
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_data = participant
                break

        if not player_data:
            continue

        stats["total_games"] += 1

        # Basic stats
        if player_data.get("win", False):
            stats["wins"] += 1
        else:
            stats["losses"] += 1

        stats["total_kills"] += player_data.get("kills", 0)
        stats["total_deaths"] += player_data.get("deaths", 0)
        stats["total_assists"] += player_data.get("assists", 0)

        # Champion and role tracking
        champion = player_data.get("championName", "Unknown")
        role = player_data.get("teamPosition", "Unknown")
        stats["champions_played"][champion] += 1
        stats["roles_played"][role] += 1

        # Game metrics
        total_duration += match["info"].get("gameDuration", 0)
        stats["total_damage"] += player_data.get("totalDamageDealtToChampions", 0)
        stats["total_gold"] += player_data.get("goldEarned", 0)

    # Calculate averages
    if stats["total_games"] > 0:
        stats["win_rate"] = stats["wins"] / stats["total_games"]
        stats["average_kda"] = (stats["total_kills"] + stats["total_assists"]) / max(
            stats["total_deaths"], 1
        )
        stats["average_game_duration"] = total_duration / stats["total_games"]
        stats["average_damage"] = stats["total_damage"] / stats["total_games"]
        stats["average_gold"] = stats["total_gold"] / stats["total_games"]

    return stats


def analyze_team_performance(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze overall team performance metrics.

    Args:
        matches (List[Dict]): List of match data

    Returns:
        Dict[str, Any]: Team performance statistics
    """
    stats = {
        "total_matches": len(matches),
        "game_modes": Counter(),
        "game_types": Counter(),
        "average_duration": 0,
        "objectives": {
            "dragons": {"total": 0, "avg_per_game": 0},
            "barons": {"total": 0, "avg_per_game": 0},
            "heralds": {"total": 0, "avg_per_game": 0},
            "towers": {"total": 0, "avg_per_game": 0},
        },
    }

    total_duration = 0

    for match in matches:
        if "info" not in match:
            continue

        info = match["info"]

        # Game mode and type tracking
        stats["game_modes"][info.get("gameMode", "Unknown")] += 1
        stats["game_types"][info.get("gameType", "Unknown")] += 1

        # Duration tracking
        duration = info.get("gameDuration", 0)
        total_duration += duration

        # Objectives tracking (sum both teams)
        if "teams" in info:
            for team in info["teams"]:
                objectives = team.get("objectives", {})
                stats["objectives"]["dragons"]["total"] += objectives.get(
                    "dragon", {}
                ).get("kills", 0)
                stats["objectives"]["barons"]["total"] += objectives.get(
                    "baron", {}
                ).get("kills", 0)
                stats["objectives"]["heralds"]["total"] += objectives.get(
                    "riftHerald", {}
                ).get("kills", 0)
                stats["objectives"]["towers"]["total"] += objectives.get(
                    "tower", {}
                ).get("kills", 0)

    # Calculate averages
    if stats["total_matches"] > 0:
        stats["average_duration"] = total_duration / stats["total_matches"]
        for obj_type in stats["objectives"]:
            stats["objectives"][obj_type]["avg_per_game"] = (
                stats["objectives"][obj_type]["total"] / stats["total_matches"]
            )

    return stats


def print_player_report(stats: Dict[str, Any], player_name: str):
    """Print a formatted player performance report."""
    print(f"\n{'='*50}")
    print(f"PLAYER PERFORMANCE REPORT: {player_name}")
    print(f"{'='*50}")

    print(f"\n📊 Overall Performance:")
    print(f"   Total Games: {stats['total_games']}")
    print(f"   Wins: {stats['wins']} | Losses: {stats['losses']}")
    print(f"   Win Rate: {stats.get('win_rate', 0):.1%}")

    print(f"\n⚔️ Combat Stats:")
    print(
        f"   Total K/D/A: {stats['total_kills']}/{stats['total_deaths']}/{stats['total_assists']}"
    )
    print(f"   Average KDA: {stats.get('average_kda', 0):.2f}")

    print(f"\n🏆 Champions (Top 5):")
    for champion, count in stats["champions_played"].most_common(5):
        print(f"   {champion}: {count} games")

    print(f"\n🎯 Preferred Roles:")
    for role, count in stats["roles_played"].most_common():
        print(f"   {role}: {count} games")

    print(f"\n💰 Performance Metrics:")
    print(f"   Average Damage: {stats.get('average_damage', 0):,.0f}")
    print(f"   Average Gold: {stats.get('average_gold', 0):,.0f}")
    print(
        f"   Average Game Duration: {stats.get('average_game_duration', 0)//60:.0f}m {stats.get('average_game_duration', 0)%60:.0f}s"
    )


def print_team_report(stats: Dict[str, Any]):
    """Print a formatted team performance report."""
    print(f"\n{'='*50}")
    print(f"TEAM PERFORMANCE ANALYSIS")
    print(f"{'='*50}")

    print(f"\n📈 Match Overview:")
    print(f"   Total Matches Analyzed: {stats['total_matches']}")
    print(
        f"   Average Game Duration: {stats['average_duration']//60:.0f}m {stats['average_duration']%60:.0f}s"
    )

    print(f"\n🎮 Game Modes:")
    for mode, count in stats["game_modes"].most_common():
        print(f"   {mode}: {count} matches")

    print(f"\n🏹 Objectives Per Game (Average):")
    for obj_type, data in stats["objectives"].items():
        print(f"   {obj_type.title()}: {data['avg_per_game']:.1f}")


def main():
    """Main function for data analysis."""

    parser = argparse.ArgumentParser(description="Analyze League of Legends match data")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--player",
        type=str,
        help="Player name to analyze (must exist in config) [legacy mode]",
    )
    group.add_argument(
        "--riot-id",
        nargs=2,
        metavar=("GAME_NAME", "TAG_LINE"),
        help="Riot ID: game name and tag line (e.g. 'Frowtch blue')",
    )
    parser.add_argument(
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
    parser.add_argument(
        "--team-analysis",
        action="store_true",
        help="Show team-wide analysis instead of player-specific",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (overrides --log-level)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging level (ignored if --debug is set)",
    )
    parser.add_argument(
        "--min-matches",
        type=int,
        default=5,
        help="Minimum local matches required for player analysis (auto-fetch if fewer)",
    )
    parser.add_argument(
        "--fetch-count",
        type=int,
        default=10,
        help="Number of matches to fetch when auto-fetch triggers",
    )
    parser.add_argument(
        "--no-auto-fetch",
        action="store_true",
        help="Disable automatic fetching of matches when insufficient local data",
    )
    args = parser.parse_args()

    # Set up logging
    level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    logger.debug("Entered main() with args: %s", args)

    # Load matches
    matches = load_match_files(args.matches_dir)
    logger.debug("Loaded %d matches from %s", len(matches), args.matches_dir)

    if args.team_analysis:
        logger.debug("Running team analysis")
        team_stats = analyze_team_performance(matches)
        print_team_report(team_stats)
        return

    # Player analysis path
    logger.debug("Running player analysis")
    if args.riot_id:
        logger.debug("Using Riot ID path")
        from stats_visualization import league

        token = os.getenv("RIOT_API_TOKEN")
        logger.debug("RIOT_API_TOKEN present: %s", bool(token))
        if not token:
            print("RIOT_API_TOKEN environment variable is not set.")
            return
        game_name, tag_line = args.riot_id
        original_label = f"{game_name}#{tag_line}"
        # Generate case-insensitive variants to try
        variants = []
        seen = set()
        game_name_variants = {
            game_name,
            game_name.lower(),
            game_name.upper(),
            game_name.title(),
        }
        tag_variants = {tag_line, tag_line.lower(), tag_line.upper()}
        for gn in game_name_variants:
            for tg in tag_variants:
                key = (gn, tg)
                if key not in seen:
                    seen.add(key)
                    variants.append(key)
        player_puuid = None
        last_error = None
        for gn_try, tg_try in variants:
            try:
                logger.debug(
                    "Attempting PUUID fetch with variant %s#%s", gn_try, tg_try
                )
                player_puuid = league.fetch_puuid_by_riot_id(gn_try, tg_try, token)
                break
            except Exception as e:
                last_error = e
                continue
        if player_puuid is None:
            print(
                f"Failed to fetch PUUID for {original_label} (case-insensitive attempts exhausted): {last_error}"
            )
            return
        player_label = original_label
    elif args.player:
        logger.debug("Using legacy player config path")
        from stats_visualization import league

        puuids = league.load_player_config()
        logger.debug("Loaded player config entries: %s", list(puuids.keys()))
        lookup = args.player.lower()
        key_map = {name.lower(): name for name in puuids.keys()}
        if lookup not in key_map:
            available_players = ", ".join(puuids.keys())
            print(f"Player '{args.player}' not found. Available: {available_players}")
            return
        resolved_name = key_map[lookup]
        player_puuid = puuids[resolved_name]
        player_label = resolved_name
    else:
        print("Please specify either --riot-id or --player (or use --team-analysis).")
        return

    # Auto-fetch logic if enabled and not enough local matches for this player
    if not args.no_auto_fetch:
        try:
            from stats_visualization import league as league_mod
            import time

            token_af = os.getenv("RIOT_API_TOKEN")
            if token_af:
                prev_player_matches = _count_player_matches(matches, player_puuid)
                prev_total_files = len(matches)
                if prev_player_matches < args.min_matches:
                    logger.info(
                        "Auto-fetching matches: have %d < %d (fetch_count=%d)",
                        prev_player_matches,
                        args.min_matches,
                        args.fetch_count,
                    )
                    started = time.time()
                    try:
                        league_mod.ensure_matches_for_player(
                            player_puuid,
                            token_af,
                            matches_dir=args.matches_dir,
                            min_matches=args.min_matches,
                            fetch_count=args.fetch_count,
                        )
                        duration = time.time() - started
                        # Reload matches after fetch
                        matches = load_match_files(args.matches_dir)
                        new_player_matches = _count_player_matches(
                            matches, player_puuid
                        )
                        new_total_files = len(matches)
                        delta_player = new_player_matches - prev_player_matches
                        delta_files = new_total_files - prev_total_files
                        print(
                            f"\n✅ Fetch complete in {duration:.1f}s: player matches {prev_player_matches} -> {new_player_matches} (+{delta_player}); files {prev_total_files} -> {new_total_files} (+{delta_files})."
                        )
                        if new_player_matches < args.min_matches:
                            print(
                                f"⚠️ Still below desired minimum ({new_player_matches} < {args.min_matches}). Consider increasing --fetch-count and re-running."
                            )
                        elif delta_player == 0:
                            print("ℹ️ No new matches involving this player were added.")
                    except Exception as e:
                        logger.warning("Auto-fetch failed: %s", e)
                else:
                    logger.debug(
                        "Skipping auto-fetch: already have %d >= %d player matches",
                        prev_player_matches,
                        args.min_matches,
                    )
            else:
                logger.debug("Skipping auto-fetch: RIOT_API_TOKEN not set")
        except Exception as e:
            logger.debug("Auto-fetch setup encountered an error: %s", e)

    logger.debug("Analyzing player %s", player_label)
    player_stats = analyze_player_performance(matches, player_puuid)
    logger.debug("Player stats computed: %s", player_stats)
    if player_stats["total_games"] == 0:
        print(f"No matches found for player {player_label}")
        return
    print_player_report(player_stats, player_label)


if __name__ == "__main__":  # ensure CLI works
    main()
