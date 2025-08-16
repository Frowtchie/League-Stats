#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jungle clear time analysis visualization module for League of Legends match data.
Analyzes first jungle clear times for jungle role games using timeline data.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict
import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from stats_visualization import league
from stats_visualization import analyze
from stats_visualization.viz_types import JungleData
from stats_visualization.utils import filter_matches


def extract_jungle_clear_data(
    player_puuid: str,
    matches_dir: str = "matches",
    include_aram: bool = False,
    queue_filter: list[int] | None = None,
    game_mode_whitelist: list[str] | None = None,
) -> JungleData:
    """
    Extract jungle clear time data for a specific player.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing jungle clear statistics
    """
    raw_matches = analyze.load_match_files(matches_dir)
    matches = filter_matches(
        raw_matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )
    jungle_data: JungleData = {
        "first_clear_times": [],
        "champions": [],
        "wins": [],
        "game_durations": [],
        "clear_efficiency": [],  # CS per minute in early game
        "total_games": 0,
        "jungle_games": 0,
    }

    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue

        # Find player data in this match
        player_data = None
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_data = participant
                break

        if not player_data:
            continue

        jungle_data["total_games"] += 1

        # Check if player was jungling in this game
        role = player_data.get("teamPosition", "")
        if role != "JUNGLE":
            continue

        jungle_data["jungle_games"] += 1

        # Calculate first clear time using available data
        clear_time = calculate_first_clear_time(match, player_data)

        if clear_time is not None:
            jungle_data["first_clear_times"].append(clear_time)
            jungle_data["champions"].append(player_data.get("championName", "Unknown"))
            jungle_data["wins"].append(player_data.get("win", False))

            game_duration = match["info"].get("gameDuration", 0)
            jungle_data["game_durations"].append(
                game_duration / 60
            )  # Convert to minutes

            # Calculate early game efficiency (neutral minions killed as proxy)
            neutral_cs = player_data.get("neutralMinionsKilled", 0)
            duration_minutes = game_duration / 60 if game_duration > 0 else 1
            efficiency = neutral_cs / duration_minutes
            jungle_data["clear_efficiency"].append(efficiency)

    return jungle_data


def calculate_first_clear_time(
    match: Dict[str, Any], player_data: Dict[str, Any]
) -> Optional[float]:
    """
    Calculate the first jungle clear time using available match data.

    Since timeline data might not be available, we use heuristics based on:
    - Game duration and neutral minions killed
    - Typical clear times for different champions
    - Early game performance indicators

    Args:
        match (Dict): Match data
        player_data (Dict): Player's participant data

    Returns:
        Optional[float]: Estimated first clear time in minutes, or None if not determinable
    """
    # Check if timeline data is available
    if "timeline" in match and "frames" in match["timeline"]:
        return calculate_clear_time_from_timeline(match["timeline"], player_data)

    # Fallback: Estimate based on champion and neutral CS
    return estimate_clear_time_from_stats(player_data)


def calculate_clear_time_from_timeline(
    timeline: Dict[str, Any], player_data: Dict[str, Any]
) -> Optional[float]:
    """
    Calculate first clear time from timeline events.

    Args:
        timeline (Dict): Timeline data from match
        player_data (Dict): Player's participant data

    Returns:
        Optional[float]: First clear time in minutes
    """
    participant_id = player_data.get("participantId")
    if not participant_id:
        return None

    # Track jungle monster kills for this participant
    jungle_kills = []
    frames = timeline.get("frames", [])

    for frame in frames:
        timestamp = frame.get("timestamp", 0) / 1000 / 60  # Convert to minutes

        # Check events in this frame
        for event in frame.get("events", []):
            if (
                event.get("type") == "ELITE_MONSTER_KILL"
                or event.get("type") == "NEUTRAL_MONSTER_KILL"
            ):

                killer_id = event.get("killerId")
                if killer_id == participant_id:
                    monster_type = event.get("monsterType", "")
                    jungle_kills.append(
                        {"timestamp": timestamp, "monster_type": monster_type}
                    )

    # Determine if a full clear was completed
    # Look for key jungle monsters: Blue, Red, Gromp, Krugs, Raptors, Wolves
    if jungle_kills:
        # Sort by timestamp
        jungle_kills.sort(key=lambda x: x["timestamp"])

        # Simple heuristic: if 4+ jungle monsters killed in first 5 minutes,
        # consider the time of the 4th kill as clear completion
        early_kills = [k for k in jungle_kills if k["timestamp"] <= 5.0]
        if len(early_kills) >= 4:
            return early_kills[3]["timestamp"]  # 4th kill timestamp

    return None


def estimate_clear_time_from_stats(player_data: Dict) -> Optional[float]:
    """
    Estimate clear time based on champion and performance stats.

    Args:
        player_data (Dict): Player's participant data

    Returns:
        Optional[float]: Estimated clear time in minutes
    """
    champion = player_data.get("championName", "")
    neutral_cs = player_data.get("neutralMinionsKilled", 0)

    # If very low neutral CS, likely didn't jungle properly
    if neutral_cs < 10:
        return None

    # Champion-based estimates (typical first clear times)
    fast_clearers = ["Graves", "Karthus", "Morgana", "Fiddlesticks", "Shyvana"]
    medium_clearers = ["Lee Sin", "Elise", "Jarvan IV", "Xin Zhao", "Warwick"]
    slow_clearers = ["Rammus", "Sejuani", "Zac", "Amumu"]

    if champion in fast_clearers:
        base_time = 3.2  # minutes
    elif champion in medium_clearers:
        base_time = 3.5
    elif champion in slow_clearers:
        base_time = 4.0
    else:
        base_time = 3.6  # Default estimate

    # Add some variance based on performance
    # Higher CS efficiency suggests faster clear
    total_cs = player_data.get("totalMinionsKilled", 0) + neutral_cs
    if total_cs > 150:  # Above average CS
        base_time -= 0.2
    elif total_cs < 100:  # Below average CS
        base_time += 0.3

    return base_time


from stats_visualization.viz_types import JungleData


def plot_jungle_clear_analysis(
    player_name: str, jungle_data: JungleData | Dict[str, Any]
):
    """
    Create comprehensive jungle clear time visualizations.

    Args:
        player_name (str): Name of the player
        jungle_data (Dict): Jungle performance data
    """
    if jungle_data["jungle_games"] == 0:
        print(f"No jungle games found for {player_name}")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(
        f"{player_name} - Jungle Clear Analysis", fontsize=16, fontweight="bold"
    )

    # 1. First Clear Time Distribution
    if jungle_data["first_clear_times"]:
        clear_times = jungle_data["first_clear_times"]
        ax1.hist(
            clear_times, bins=10, alpha=0.7, color="forestgreen", edgecolor="black"
        )
        ax1.set_xlabel("First Clear Time (minutes)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("First Clear Time Distribution")

        # Add average line
        avg_time = np.mean(clear_times)
        ax1.axvline(
            avg_time,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Average: {avg_time:.2f} min",
        )
        ax1.legend()

        # Add statistics text
        stats_text = f"Games: {len(clear_times)}\nAvg: {avg_time:.2f} min\nBest: {min(clear_times):.2f} min"
        ax1.text(
            0.02,
            0.98,
            stats_text,
            transform=ax1.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )
    else:
        ax1.text(
            0.5,
            0.5,
            "No clear time data available",
            ha="center",
            va="center",
            transform=ax1.transAxes,
            fontsize=12,
        )
        ax1.set_title("First Clear Time Distribution")

    # 2. Clear Time by Champion
    if jungle_data["first_clear_times"] and jungle_data["champions"]:
        champion_times = defaultdict(list)
        for time, champ in zip(
            jungle_data["first_clear_times"], jungle_data["champions"]
        ):
            champion_times[champ].append(time)

        # Only show champions with 2+ games
        filtered_champions = {
            champ: times for champ, times in champion_times.items() if len(times) >= 2
        }

        if filtered_champions:
            champ_names = list(filtered_champions.keys())
            avg_times = [np.mean(times) for times in filtered_champions.values()]
            colors = plt.cm.Set3(np.linspace(0, 1, len(champ_names)))

            bars = ax2.bar(
                champ_names, avg_times, color=colors, alpha=0.8, edgecolor="black"
            )
            ax2.set_xlabel("Champion")
            ax2.set_ylabel("Average Clear Time (minutes)")
            ax2.set_title("Average Clear Time by Champion")
            ax2.tick_params(axis="x", rotation=45)

            # Add value labels on bars
            for bar, avg in zip(bars, avg_times):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    f"{avg:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
        else:
            ax2.text(
                0.5,
                0.5,
                "Insufficient champion data\n(need 2+ games per champion)",
                ha="center",
                va="center",
                transform=ax2.transAxes,
                fontsize=10,
            )
            ax2.set_title("Average Clear Time by Champion")
    else:
        ax2.text(
            0.5,
            0.5,
            "No champion data available",
            ha="center",
            va="center",
            transform=ax2.transAxes,
            fontsize=12,
        )
        ax2.set_title("Average Clear Time by Champion")

    # 3. Clear Time vs Win Rate
    if jungle_data["first_clear_times"] and jungle_data["wins"]:
        # Create bins for clear times
        clear_times = np.array(jungle_data["first_clear_times"])
        wins = np.array(jungle_data["wins"])

        # Sort by clear time and group into bins
        sorted_indices = np.argsort(clear_times)
        sorted_times = clear_times[sorted_indices]
        sorted_wins = wins[sorted_indices]

        # Create 4 bins (quartiles)
        n_bins = min(4, len(sorted_times))
        bin_size = len(sorted_times) // n_bins

        bin_centers = []
        win_rates = []

        for i in range(n_bins):
            start_idx = i * bin_size
            if i == n_bins - 1:  # Last bin gets remaining data
                end_idx = len(sorted_times)
            else:
                end_idx = (i + 1) * bin_size

            bin_times = sorted_times[start_idx:end_idx]
            bin_wins = sorted_wins[start_idx:end_idx]

            if len(bin_times) > 0:
                bin_centers.append(np.mean(bin_times))
                win_rates.append(np.mean(bin_wins) * 100)

        if bin_centers:
            ax3.scatter(bin_centers, win_rates, s=100, alpha=0.7, color="blue")
            ax3.plot(bin_centers, win_rates, "--", alpha=0.5, color="blue")
            ax3.set_xlabel("Clear Time (minutes)")
            ax3.set_ylabel("Win Rate (%)")
            ax3.set_title("Win Rate vs Clear Time")
            ax3.grid(True, alpha=0.3)

            # Add trend line
            if len(bin_centers) > 1:
                z = np.polyfit(bin_centers, win_rates, 1)
                p = np.poly1d(z)
                ax3.plot(
                    bin_centers,
                    p(bin_centers),
                    "r--",
                    alpha=0.8,
                    label=f"Trend: {z[0]:.1f}% per min",
                )
                ax3.legend()
        else:
            ax3.text(
                0.5,
                0.5,
                "Insufficient data for analysis",
                ha="center",
                va="center",
                transform=ax3.transAxes,
                fontsize=10,
            )
            ax3.set_title("Win Rate vs Clear Time")
    else:
        ax3.text(
            0.5,
            0.5,
            "No win rate data available",
            ha="center",
            va="center",
            transform=ax3.transAxes,
            fontsize=12,
        )
        ax3.set_title("Win Rate vs Clear Time")

    # 4. Summary Statistics
    ax4.axis("off")
    summary_text = f"""Jungle Performance Summary

Total Games Analyzed: {jungle_data['total_games']}
Jungle Games: {jungle_data['jungle_games']}

"""

    if jungle_data["first_clear_times"]:
        clear_times = jungle_data["first_clear_times"]
        avg_time = np.mean(clear_times)
        best_time = min(clear_times)
        worst_time = max(clear_times)

        summary_text += f"""Clear Time Statistics:
• Average: {avg_time:.2f} minutes
• Best: {best_time:.2f} minutes
• Worst: {worst_time:.2f} minutes
• Games with data: {len(clear_times)}

"""

    if jungle_data["wins"]:
        wins = jungle_data["wins"]
        win_rate = np.mean(wins) * 100
        summary_text += f"Win Rate: {win_rate:.1f}% ({sum(wins)}/{len(wins)})"

    ax4.text(
        0.05,
        0.95,
        summary_text,
        transform=ax4.transAxes,
        fontsize=11,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=1", facecolor="lightgray", alpha=0.8),
    )

    plt.tight_layout()
    # Save using plt.savefig so tests that patch matplotlib.pyplot.savefig detect the call
    output_path = Path("output") / "jungle_clear_analysis.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved jungle clear analysis to {output_path}")
    plt.show()


def main():
    """Main function for jungle clear analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze jungle clear times for League of Legends matches"
    )
    parser.add_argument(
        "game_name", type=str, help="Riot in-game name (IGN) (e.g. frowtch)"
    )
    parser.add_argument("tag_line", type=str, help="Riot tag line (e.g. blue)")
    parser.add_argument(
        "-m",
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
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
        help="Restrict to queue IDs (e.g. 420 440)",
    )
    parser.add_argument(
        "-R", "--ranked-only", action="store_true", help="Shortcut for --queue 420 440"
    )
    parser.add_argument(
        "-M",
        "--modes",
        nargs="*",
        help="Whitelist gameMode values (e.g. CLASSIC CHERRY)",
    )
    parser.add_argument(
        "-O",
        "--no-clean-output",
        action="store_true",
        help="Do not delete existing PNGs in output/ (default behavior is to clean)",
    )

    args = parser.parse_args()

    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        print("RIOT_API_TOKEN environment variable is not set.")
        return

    puuids = league.load_player_config()
    player_key = args.game_name
    player_display = f"{args.game_name}#{args.tag_line}"
    player_puuid = puuids.get(player_key)

    if not player_puuid:
        try:
            player_puuid = league.fetch_puuid_by_riot_id(
                args.game_name, args.tag_line, token
            )
            print(f"Fetched PUUID for {player_display}")
        except Exception:
            print(
                f"Player '{player_display}' not found in config and could not fetch from Riot API."
            )
            return

    matches_dir = args.matches_dir
    # Ensure there are matches for this player, fetch if needed
    num_matches = league.ensure_matches_for_player(
        player_puuid, token, matches_dir, min_matches=1, fetch_count=10
    )
    if num_matches == 0:
        print(f"Failed to fetch or find any matches for {player_display}.")
        return

    from stats_visualization.utils import clean_output

    if not args.no_clean_output:
        clean_output()

    print(f"Analyzing jungle clear times for {player_display}...")
    queue_filter = args.queue
    if args.ranked_only and queue_filter is None:
        queue_filter = [420, 440]
    jungle_data = extract_jungle_clear_data(
        player_puuid,
        matches_dir,
        include_aram=args.include_aram,
        queue_filter=queue_filter,
        game_mode_whitelist=args.modes,
    )

    # Create visualization
    plot_jungle_clear_analysis(player_display, jungle_data)

    # Print summary to console
    print(f"\n=== Jungle Clear Analysis for {player_display} ===")
    print(f"Total games: {jungle_data['total_games']}")
    print(f"Jungle games: {jungle_data['jungle_games']}")

    if jungle_data["first_clear_times"]:
        clear_times = jungle_data["first_clear_times"]
        print(f"Games with clear time data: {len(clear_times)}")
        print(f"Average first clear time: {np.mean(clear_times):.2f} minutes")
        print(f"Best clear time: {min(clear_times):.2f} minutes")
        print(
            f"Fastest clearing champion: {jungle_data['champions'][np.argmin(clear_times)]}"
        )
    else:
        print("No clear time data available")
        print("Note: This analysis requires timeline data or uses estimation methods")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during analysis: {e}")
        exit(1)
