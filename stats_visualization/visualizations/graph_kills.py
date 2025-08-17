#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Personal kills statistics visualization for League of Legends match data.
Analyzes kill performance and progression from personal match history.
"""


import os
import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Optional, List
import datetime  # noqa: F401
import datetime
from dotenv import load_dotenv


# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))  # noqa: E402
from stats_visualization import league
from stats_visualization import analyze
from stats_visualization.viz_types import KillsData, ChampionStats
from stats_visualization.utils import filter_matches, save_figure, sanitize_player

# Load environment variables from config.env if present
load_dotenv(dotenv_path="config.env")


def extract_kills_data(
    player_puuid: str,
    matches_dir: str = "matches",
    include_aram: bool = False,
    queue_filter: Optional[List[int]] = None,
    game_mode_whitelist: Optional[List[str]] = None,
) -> KillsData:
    """
    Extract kills data for a specific player from match history.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing kills statistics
    """
    print(f"[DEBUG] extract_kills_data called with player_puuid={player_puuid}")
    raw_matches = analyze.load_match_files(matches_dir)
    print(f"[DEBUG] [extract_kills_data] raw_matches loaded: {raw_matches}")
    matches = filter_matches(
        raw_matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )
    print(f"[DEBUG] [extract_kills_data] matches after filter: {matches}")
    kills_data: KillsData = {
        "kills": [],
        "deaths": [],
        "assists": [],
        "kda_ratios": [],
        "kill_participation": [],
        "game_dates": [],
        "game_durations": [],
        "champions": [],
        "wins": [],
        "total_games": 0,
    }
    for match in matches:
        print(f"[DEBUG] processing match: {match}")

    # Always return kills_data, even if matches is empty
    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue
        player_data = None
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_data = participant
                break
        if not player_data:
            continue
        kills_data["total_games"] += 1
        game_creation = match["info"].get("gameCreation", 0)
        if game_creation > 0:
            game_date = datetime.datetime.fromtimestamp(game_creation / 1000)
            kills_data["game_dates"].append(game_date)
        else:
            kills_data["game_dates"].append(datetime.datetime.now())
        game_duration = match["info"].get("gameDuration", 0)
        kills_data["game_durations"].append(game_duration / 60)
        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        kills_data["kills"].append(kills)
        kills_data["deaths"].append(deaths)
        kills_data["assists"].append(assists)
        kda = (kills + assists) / max(deaths, 1)
        kills_data["kda_ratios"].append(kda)
        team_kills = 0
        player_team_id = player_data.get("teamId")
        if "participants" in match["info"]:
            for participant in match["info"]["participants"]:
                if participant.get("teamId") == player_team_id:
                    team_kills += participant.get("kills", 0)
        kill_participation = (kills + assists) / max(team_kills, 1) * 100
        kills_data["kill_participation"].append(kill_participation)
        kills_data["champions"].append(player_data.get("championName", "Unknown"))
        kills_data["wins"].append(player_data.get("win", False))
    for key in [
        "kills",
        "deaths",
        "assists",
        "kda_ratios",
        "kill_participation",
        "game_dates",
        "game_durations",
        "champions",
        "wins",
        "total_games",
    ]:
        if key not in kills_data:
            kills_data[key] = [] if key != "total_games" else 0
    print(f"[DEBUG] extract_kills_data returning: {kills_data}")
    return dict(kills_data)


def plot_kills_analysis(player_name: str, kills_data: KillsData) -> None:
    """
    Create comprehensive kills analysis visualization.
    """
    if kills_data["total_games"] == 0:
        print(f"No games found for {player_name}")
        plt.figure(figsize=(8, 4))
        plt.suptitle(f"No games found for {player_name}")
        plt.show()
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Kills progression over time
    game_numbers = range(1, len(kills_data["kills"]) + 1)
    ax1.plot(game_numbers, kills_data["kills"], "o-", alpha=0.7, color="red", label="Kills")
    ax1.plot(
        game_numbers,
        kills_data["assists"],
        "s-",
        alpha=0.7,
        color="blue",
        label="Assists",
    )

    # Add trend lines
    if len(kills_data["kills"]) > 1:
        kills_trend = np.polyfit(game_numbers, kills_data["kills"], 1)
        assists_trend = np.polyfit(game_numbers, kills_data["assists"], 1)

        ax1.plot(
            game_numbers,
            np.poly1d(kills_trend)(game_numbers),
            "--",
            alpha=0.8,
            color="darkred",
            label=f"Kills trend: {kills_trend[0]:.2f}/game",
        )
        ax1.plot(
            game_numbers,
            np.poly1d(assists_trend)(game_numbers),
            "--",
            alpha=0.8,
            color="darkblue",
            label=f"Assists trend: {assists_trend[0]:.2f}/game",
        )

    ax1.set_xlabel("Game Number")
    ax1.set_ylabel("Count")
    ax1.set_title(f"{player_name} - Kills & Assists Over Time")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # KDA distribution
    ax2.hist(kills_data["kda_ratios"], bins=15, alpha=0.7, color="green", edgecolor="black")
    avg_kda = np.mean(kills_data["kda_ratios"])
    ax2.axvline(avg_kda, color="red", linestyle="--", label=f"Average KDA: {avg_kda:.2f}")
    ax2.set_xlabel("KDA Ratio")
    ax2.set_ylabel("Number of Games")
    ax2.set_title(f"{player_name} - KDA Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Kill participation over time
    ax3.plot(game_numbers, kills_data["kill_participation"], "o-", alpha=0.7, color="purple")
    avg_kp = np.mean(kills_data["kill_participation"])
    ax3.axhline(avg_kp, color="red", linestyle="--", label=f"Average KP: {avg_kp:.1f}%")
    ax3.set_xlabel("Game Number")
    ax3.set_ylabel("Kill Participation (%)")
    ax3.set_title(f"{player_name} - Kill Participation Over Time")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)

    # Performance by game outcome
    win_kills = [k for k, w in zip(kills_data["kills"], kills_data["wins"]) if w]
    loss_kills = [k for k, w in zip(kills_data["kills"], kills_data["wins"]) if not w]
    # Retained for potential future use (e.g., deeper outcome-based KDA comparison)
    win_kda = [
        kda for kda, w in zip(kills_data["kda_ratios"], kills_data["wins"]) if w
    ]  # noqa: F841
    loss_kda = [
        kda for kda, w in zip(kills_data["kda_ratios"], kills_data["wins"]) if not w
    ]  # noqa: F841

    # Box plot comparison
    data_to_plot = []
    labels = []

    if win_kills:
        data_to_plot.append(win_kills)
        labels.append(f"Wins\n({len(win_kills)} games)")
    if loss_kills:
        data_to_plot.append(loss_kills)
        labels.append(f"Losses\n({len(loss_kills)} games)")

    if data_to_plot:
        bp = ax4.boxplot(data_to_plot, tick_labels=labels, patch_artist=True)
        colors = ["lightgreen", "lightcoral"]
        for patch, color in zip(bp["boxes"], colors[: len(bp["boxes"])]):
            patch.set_facecolor(color)

        ax4.set_ylabel("Kills per Game")
        ax4.set_title(f"{player_name} - Kills by Game Outcome")
        ax4.grid(True, alpha=0.3)

    save_figure(
        plt.gcf(),
        f"kills_analysis_{sanitize_player(player_name)}",
        description="kills analysis",
    )
    plt.show()


def plot_detailed_performance(player_name: str, kills_data: KillsData) -> None:
    """
    Create detailed performance analysis with champion breakdown.
    """
    if kills_data["total_games"] == 0:
        return

    # Champion performance analysis
    from collections import defaultdict

    champion_stats: Dict[str, ChampionStats] = defaultdict(
        lambda: {"kills": [], "deaths": [], "assists": [], "kda": [], "games": 0}
    )

    for i, champion in enumerate(kills_data["champions"]):
        champion_stats[champion]["kills"].append(kills_data["kills"][i])
        champion_stats[champion]["deaths"].append(kills_data["deaths"][i])
        champion_stats[champion]["assists"].append(kills_data["assists"][i])
        champion_stats[champion]["kda"].append(kills_data["kda_ratios"][i])
        champion_stats[champion]["games"] += 1

    # Filter champions with at least 2 games
    filtered_champions = {
        champ: stats for champ, stats in champion_stats.items() if stats["games"] >= 2
    }

    if not filtered_champions:
        print(f"No champions with enough games for detailed analysis")
        return

    # Get top 6 most played champions
    top_champions = dict(
        sorted(filtered_champions.items(), key=lambda x: x[1]["games"], reverse=True)[:6]
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Average KDA by champion
    champions = list(top_champions.keys())
    avg_kdas = [np.mean(stats["kda"]) for stats in top_champions.values()]
    games_count = [stats["games"] for stats in top_champions.values()]

    bars1 = ax1.bar(champions, avg_kdas, color="skyblue", alpha=0.7)
    ax1.set_ylabel("Average KDA")
    ax1.set_title(f"{player_name} - Average KDA by Champion")
    ax1.tick_params(axis="x", rotation=45)

    # Add game count labels
    for bar, games in zip(bars1, games_count):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.05,
            f"{games} games",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Kill distribution by champion (box plot)
    champion_kills = [top_champions[champ]["kills"] for champ in champions]
    bp = ax2.boxplot(champion_kills, tick_labels=champions, patch_artist=True)

    colors = plt.cm.Set3(np.linspace(0, 1, len(champions)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)

    ax2.set_ylabel("Kills per Game")
    ax2.set_title(f"{player_name} - Kill Distribution by Champion")
    ax2.tick_params(axis="x", rotation=45)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def main():
    """Main function for kills analysis visualization."""

    parser = argparse.ArgumentParser(description="Generate personal kills statistics visualization")
    parser.add_argument("game_name", type=str, help="Riot in-game name (IGN) (e.g. frowtch)")
    parser.add_argument("tag_line", type=str, help="Riot tag line (e.g. blue)")
    parser.add_argument(
        "-m",
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
    parser.add_argument(
        "-D", "--detailed", action="store_true", help="Show detailed champion breakdown"
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
            player_puuid = league.fetch_puuid_by_riot_id(args.game_name, args.tag_line, token)
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

    print(f"Analyzing kills data for {player_display}...")
    queue_filter = args.queue
    if args.ranked_only and queue_filter is None:
        queue_filter = [420, 440]
    kills_data = extract_kills_data(
        player_puuid,
        matches_dir,
        include_aram=args.include_aram,
        queue_filter=queue_filter,
        game_mode_whitelist=args.modes,
    )

    if kills_data["total_games"] == 0:
        print(f"No matches found for {player_display}")
        return

    # Generate visualization
    plot_kills_analysis(player_display, kills_data)

    if args.detailed:
        plot_detailed_performance(player_display, kills_data)


if __name__ == "__main__":
    main()
