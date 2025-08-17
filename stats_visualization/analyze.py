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
from typing import Dict, List, Any, Iterable, Optional
from collections import Counter
import logging

# Allow running as a script (python stats_visualization/analyze.py) by adding project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT)) if str(PROJECT_ROOT) not in sys.path else None

logger = logging.getLogger(__name__)

try:
    # Import shared match filtering (used across visualization scripts)
    from stats_visualization.utils import filter_matches  # type: ignore
except Exception:  # pragma: no cover - fallback if path issues
    filter_matches = None  # type: ignore


def apply_analysis_filters(
    matches: List[Dict[str, Any]],
    *,
    include_aram: bool = False,
    queue_filter: Optional[Iterable[int]] = None,
    game_mode_whitelist: Optional[Iterable[str]] = None,
) -> List[Dict[str, Any]]:
    """Apply centralized match filtering for analyze CLI.

    Mirrors visualization scripts: ARAM excluded by default; optional queue & gameMode whitelists.
    If filtering utility unavailable, returns matches unchanged.
    """
    if filter_matches is None:
        return matches
    return filter_matches(
        matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )


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
    matches: List[Dict[str, Any]] = []
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


def analyze_player_performance(matches: List[Dict[str, Any]], player_puuid: str) -> Dict[str, Any]:
    """
    Analyze performance statistics for a specific player.

    Args:
        matches (List[Dict]): List of match data
        player_puuid (str): PUUID of the player to analyze

    Returns:
        Dict[str, Any]: Performance statistics
    """
    stats: Dict[str, Any] = {
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
    stats: Dict[str, Any] = {
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
                stats["objectives"]["dragons"]["total"] += objectives.get("dragon", {}).get(
                    "kills", 0
                )
                stats["objectives"]["barons"]["total"] += objectives.get("baron", {}).get(
                    "kills", 0
                )
                stats["objectives"]["heralds"]["total"] += objectives.get("riftHerald", {}).get(
                    "kills", 0
                )
                stats["objectives"]["towers"]["total"] += objectives.get("tower", {}).get(
                    "kills", 0
                )

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
    avg_duration = stats.get("average_game_duration", 0)
    print(f"   Average Game Duration: {int(avg_duration // 60):.0f}m {int(avg_duration % 60):.0f}s")


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
        "-p",
        "--player",
        type=str,
        help="Player name to analyze (must exist in config) [legacy mode]",
    )
    group.add_argument(
        "-i",
        "--riot-id",
        nargs=2,
        metavar=("IGN", "TAG_LINE"),
        help="Riot ID: in-game name (IGN) and tag line (e.g. 'Frowtch blue')",
    )
    parser.add_argument(
        "-m",
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
    parser.add_argument(
        "-t",
        "--team-analysis",
        action="store_true",
        help="Show team-wide analysis instead of player-specific",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging (overrides --log-level)",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging level (ignored if --debug is set)",
    )
    parser.add_argument(
        "-n",
        "--min-matches",
        type=int,
        default=5,
        help="Minimum local matches required for player analysis (auto-fetch if fewer)",
    )
    parser.add_argument(
        "-f",
        "--fetch-count",
        type=int,
        default=10,
        help="Number of matches to fetch when auto-fetch triggers",
    )
    parser.add_argument(
        "-X",
        "--no-auto-fetch",
        action="store_true",
        help="Disable automatic fetching of matches when insufficient local data",
    )
    # Filtering flags (aligned with visualization scripts)
    parser.add_argument(
        "-a",
        "--include-aram",
        action="store_true",
        help="Include ARAM matches (excluded by default)",
    )
    parser.add_argument(
        "-q",
        "--queue",
        type=int,
        nargs="*",
        help="Restrict to queue IDs (e.g. 420 440). If omitted, all queues included.",
    )
    parser.add_argument(
        "-R",
        "--ranked-only",
        action="store_true",
        help="Shortcut for --queue 420 440 (Ranked Solo/Duo + Flex)",
    )
    parser.add_argument(
        "-M",
        "--modes",
        nargs="*",
        help="Whitelist gameMode values (e.g. CLASSIC CHERRY). If provided, must match exactly.",
    )
    parser.add_argument(
        "-g",
        "--generate-visuals",
        action="store_true",
        help="After analysis, generate all visualization charts (drakes, barons/heralds, kills, farming, jungle clear, objectives, personal performance).",
    )
    parser.add_argument(
        "-O",
        "--no-clean-output",
        action="store_true",
        help="Do not delete existing PNGs before generating visuals when --generate-visuals is used (default is to clean).",
    )
    args = parser.parse_args()

    # Set up logging
    level = logging.DEBUG if args.debug else getattr(logging, args.log_level)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    logger.debug("Entered main() with args: %s", args)

    # Load matches (unfiltered first for potential auto-fetch logic)
    matches = load_match_files(args.matches_dir)
    logger.debug("Loaded %d raw matches from %s", len(matches), args.matches_dir)

    # Derive queue filter list (ranked-only shortcut)
    queue_filter = args.queue
    if args.ranked_only and queue_filter is None:
        queue_filter = [420, 440]

    # Apply filters early for team analysis path
    filtered_matches = apply_analysis_filters(
        matches,
        include_aram=args.include_aram,
        queue_filter=queue_filter,
        game_mode_whitelist=args.modes,
    )
    logger.debug("Filtered matches: %d (from %d)", len(filtered_matches), len(matches))

    if args.team_analysis:
        logger.debug("Running team analysis")
        team_stats = analyze_team_performance(filtered_matches)
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
        variants: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
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
                logger.debug("Attempting PUUID fetch with variant %s#%s", gn_try, tg_try)
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
                        # Re-apply filters after fetch
                        filtered_matches = apply_analysis_filters(
                            matches,
                            include_aram=args.include_aram,
                            queue_filter=queue_filter,
                            game_mode_whitelist=args.modes,
                        )
                        new_player_matches = _count_player_matches(matches, player_puuid)
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
    player_stats = analyze_player_performance(filtered_matches, player_puuid)
    logger.debug("Player stats computed: %s", player_stats)
    if player_stats["total_games"] == 0:
        print(f"No matches found for player {player_label}")
        return
    print_player_report(player_stats, player_label)

    # Optional bulk visualization generation
    if args.generate_visuals:
        if args.team_analysis:
            print("--generate-visuals ignored in team analysis mode.")
            return
        try:
            generate_all_visuals(
                player_label,
                player_puuid,
                include_aram=args.include_aram,
                queue_filter=queue_filter,
                game_mode_whitelist=args.modes,
                clean=not args.no_clean_output,
                matches_dir=args.matches_dir,
            )
        except Exception as e:  # pragma: no cover - broad safety
            logger.error("Visualization generation failed: %s", e)
            print(f"Visualization generation failed: {e}")


def generate_all_visuals(
    player_label: str,
    player_puuid: str,
    *,
    include_aram: bool = False,
    queue_filter: Optional[Iterable[int]] = None,
    game_mode_whitelist: Optional[Iterable[str]] = None,
    clean: bool = True,
    matches_dir: str = "matches",
) -> None:
    """Generate the full suite of visualization charts for a player.

    Imports each visualization module lazily and invokes its extraction + plot routines.
    A single optional output directory cleanup occurs at the start to avoid wiping
    newly created charts mid-run (visual scripts normally auto-clean individually).

    Args:
        player_label: Display label (e.g. Frowtch#blue)
        player_puuid: Player unique identifier
        include_aram / queue_filter / game_mode_whitelist: Filtering options
        clean: If True, remove existing PNGs before generation
        matches_dir: Directory with match JSONs
    """
    from stats_visualization.utils import clean_output, sanitize_player, save_figure  # type: ignore

    print("\n=== Generating visualization suite ===")
    if clean:
        clean_output()

    # Track successes / failures
    results: list[tuple[str, str]] = []

    from typing import Callable

    def _run(name: str, func: Callable[[], None]):
        try:
            func()
            results.append((name, "ok"))
        except Exception as exc:  # pragma: no cover - defensive
            results.append((name, f"fail: {exc}"))

    # 1. Personal performance (trends, champions, roles)
    from stats_visualization.visualizations import personal_performance as _pp  # type: ignore

    _run(
        "personal_trends",
        lambda: _pp.plot_performance_trends(
            player_puuid,
            player_label,
            matches_dir,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter is not None else None,
            game_mode_whitelist=(
                list(game_mode_whitelist) if game_mode_whitelist is not None else None
            ),
        ),
    )
    _run(
        "personal_champions",
        lambda: _pp.plot_champion_performance(
            player_puuid,
            player_label,
            matches_dir,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter is not None else None,
            game_mode_whitelist=(
                list(game_mode_whitelist) if game_mode_whitelist is not None else None
            ),
        ),
    )
    _run(
        "personal_roles",
        lambda: _pp.plot_role_performance(
            player_puuid,
            player_label,
            matches_dir,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter is not None else None,
            game_mode_whitelist=(
                list(game_mode_whitelist) if game_mode_whitelist is not None else None
            ),
        ),
    )

    # 2. Kills
    from stats_visualization.visualizations import graph_kills as _gk  # type: ignore

    _run(
        "kills",
        lambda: _gk.plot_kills_analysis(
            player_label,
            _gk.extract_kills_data(
                player_puuid,
                matches_dir,
                include_aram=include_aram,
                queue_filter=list(queue_filter) if queue_filter else None,
                game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
            ),
        ),
    )

    # 3. Drake control
    from stats_visualization.visualizations import graph_drakes as _gd  # type: ignore

    _run(
        "drakes",
        lambda: _gd.plot_drake_analysis(
            player_label,
            _gd.extract_drake_data(
                player_puuid,
                matches_dir,
                include_aram=include_aram,
                queue_filter=list(queue_filter) if queue_filter else None,
                game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
            ),
        ),
    )

    # 4. Baron / Herald
    from stats_visualization.visualizations import graph_barons_heralds as _bh  # type: ignore

    _run(
        "barons_heralds",
        lambda: _bh.plot_baron_herald_analysis(
            player_label,
            _bh.extract_baron_herald_data(
                player_puuid,
                matches_dir,
                include_aram=include_aram,
                queue_filter=list(queue_filter) if queue_filter else None,
                game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
            ),
        ),
    )

    # 5. Objectives (control, first, correlation)
    from stats_visualization.visualizations import objective_analysis as _oa  # type: ignore

    _run(
        "objectives_control",
        lambda: _oa.plot_objective_control(
            player_label,
            _oa.extract_objective_data(
                player_puuid,
                matches_dir,
                include_aram=include_aram,
                queue_filter=list(queue_filter) if queue_filter else None,
                game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
            ),
        ),
    )
    # reuse extracted data once for the next two plots to avoid re-loading if desired
    try:
        _obj_data_cache = _oa.extract_objective_data(
            player_puuid,
            matches_dir,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter else None,
            game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
        )
    except Exception:  # pragma: no cover
        _obj_data_cache = None
    if _obj_data_cache:
        _run(
            "objectives_first",
            lambda: _oa.plot_first_objectives(player_label, _obj_data_cache),
        )
        _run(
            "objectives_correlation",
            lambda: _oa.plot_objective_win_correlation(player_label, _obj_data_cache),
        )

    # 6. Farming / economy (farming, gold, roles)
    from stats_visualization.visualizations import farming_analysis as _fa  # type: ignore

    try:
        _econ = _fa.extract_economy_data(
            player_puuid,
            matches_dir,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter else None,
            game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
        )
    except Exception:  # pragma: no cover
        _econ = None
    if _econ:
        _run("farming", lambda: _fa.plot_farming_performance(player_label, _econ))
        _run("gold_efficiency", lambda: _fa.plot_gold_efficiency(player_label, _econ))
        _run(
            "role_economy",
            lambda: _fa.plot_role_economy_comparison(player_label, _econ),
        )

    # 7. First blood / early game
    from stats_visualization.visualizations import graph_first_bloods as _fb  # type: ignore

    _run(
        "first_bloods",
        lambda: _fb.plot_first_blood_analysis(
            player_label,
            _fb.extract_early_game_data(player_puuid, matches_dir),
        ),
    )

    # 8. Jungle clear
    from stats_visualization.visualizations import jungle_clear_analysis as _jc  # type: ignore

    _run(
        "jungle_clear",
        lambda: _jc.plot_jungle_clear_analysis(
            player_label,
            _jc.extract_jungle_clear_data(
                player_puuid,
                matches_dir,
                include_aram=include_aram,
                queue_filter=list(queue_filter) if queue_filter else None,
                game_mode_whitelist=(list(game_mode_whitelist) if game_mode_whitelist else None),
            ),
        ),
    )

    # Summary
    successes = sum(1 for _, r in results if r == "ok")
    print(f"Visualization generation complete: {successes}/{len(results)} succeeded. Details: ")
    for name, status in results:
        print(f"  - {name}: {status}")


if __name__ == "__main__":  # ensure CLI works
    main()
