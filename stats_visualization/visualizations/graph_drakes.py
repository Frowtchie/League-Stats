#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Personal drake statistics visualization for League of Legends match data.
Analyzes dragon control from personal match history.
"""

import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
from typing import Optional, List
import sys

# Load environment variables from config.env if present
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from stats_visualization import league
from stats_visualization import analyze
from stats_visualization.viz_types import DrakeData
from stats_visualization.utils import filter_matches


def extract_drake_data(
    player_puuid: str,
    matches_dir: str = "matches",
    include_aram: bool = False,
    queue_filter: Optional[List[int]] = None,
    game_mode_whitelist: Optional[List[str]] = None,
) -> DrakeData:
    """
    Extract drake-related data for a specific player from match history.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing drake statistics
    """
    print(f"[DEBUG] extract_drake_data called with player_puuid={player_puuid}")
    raw_matches = analyze.load_match_files(matches_dir)
    print(f"[DEBUG] [extract_drake_data] raw_matches loaded: {raw_matches}")
    matches = filter_matches(
        raw_matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )
    print(f"[DEBUG] [extract_drake_data] matches after filter: {matches}")
    drake_data: DrakeData = {
        "player_team_drakes": [],
        "enemy_team_drakes": [],
        "wins": [],
        "game_durations": [],
        "total_games": 0,
    }
    for match in matches:
        print(f"[DEBUG] processing match: {match}")

    # Always return drake_data, even if matches is empty
    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue
        player_team_id = None
        player_won = False
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_team_id = participant.get("teamId")
                player_won = participant.get("win", False)
                break
        if player_team_id is None:
            continue
        drake_data["total_games"] += 1
        game_duration = match["info"].get("gameDuration", 0)
        drake_data["game_durations"].append(game_duration / 60)
        drake_data["wins"].append(player_won)
        if "teams" in match["info"]:
            player_drakes = 0
            enemy_drakes = 0
            for team in match["info"]["teams"]:
                dragon_kills = team.get("objectives", {}).get("dragon", {}).get("kills", 0)
                if team["teamId"] == player_team_id:
                    player_drakes = dragon_kills
                else:
                    enemy_drakes = dragon_kills
            drake_data["player_team_drakes"].append(player_drakes)
            drake_data["enemy_team_drakes"].append(enemy_drakes)
    for key in [
        "player_team_drakes",
        "enemy_team_drakes",
        "wins",
        "game_durations",
        "total_games",
    ]:
        if key not in drake_data:
            drake_data[key] = [] if key != "total_games" else 0
    print(f"[DEBUG] extract_drake_data returning: {drake_data}")
    return dict(drake_data)


def plot_drake_analysis(player_name: str, drake_data: DrakeData) -> None:
    """
    Create comprehensive drake analysis visualization.
    """
    if drake_data["total_games"] == 0:
        print(f"No games found for {player_name}")
        plt.figure(figsize=(8, 4))
        plt.suptitle(f"No games found for {player_name}")
        plt.show()
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Drake control comparison
    avg_player_drakes = np.mean(drake_data["player_team_drakes"])
    avg_enemy_drakes = np.mean(drake_data["enemy_team_drakes"])

    teams = ["Player Team", "Enemy Team"]
    avg_drakes = [avg_player_drakes, avg_enemy_drakes]
    colors = ["lightblue", "lightcoral"]

    bars1 = ax1.bar(teams, avg_drakes, color=colors, alpha=0.7)
    ax1.set_ylabel("Average Dragons per Game")
    ax1.set_title(f"{player_name} - Dragon Control Comparison")

    # Add value labels
    for bar, value in zip(bars1, avg_drakes):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.05,
            f"{value:.1f}",
            ha="center",
            va="bottom",
        )

    # Drake control distribution
    drake_diff = [
        p - e for p, e in zip(drake_data["player_team_drakes"], drake_data["enemy_team_drakes"])
    ]
    ax2.hist(drake_diff, bins=range(-6, 7), alpha=0.7, color="purple", edgecolor="black")
    ax2.axvline(0, color="red", linestyle="--", label="Even Drake Control")
    ax2.set_xlabel("Drake Advantage (Player Team - Enemy Team)")
    ax2.set_ylabel("Number of Games")
    ax2.set_title(f"{player_name} - Drake Control Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Win rate by drake control
    win_rates = {"Behind": [], "Even": [], "Ahead": []}
    for p_drakes, e_drakes, win in zip(
        drake_data["player_team_drakes"],
        drake_data["enemy_team_drakes"],
        drake_data["wins"],
    ):
        if p_drakes < e_drakes:
            win_rates["Behind"].append(win)
        elif p_drakes == e_drakes:
            win_rates["Even"].append(win)
        else:
            win_rates["Ahead"].append(win)

    categories = []
    wr_values = []
    colors = []

    for category, wins in win_rates.items():
        if wins:
            categories.append(f"{category}\n({len(wins)} games)")
            wr_values.append(sum(wins) / len(wins) * 100)
            if category == "Behind":
                colors.append("red")
            elif category == "Even":
                colors.append("yellow")
            else:
                colors.append("green")

    if categories:
        bars3 = ax3.bar(categories, wr_values, color=colors, alpha=0.7)
        ax3.set_ylabel("Win Rate (%)")
        ax3.set_title(f"{player_name} - Win Rate by Drake Control")
        ax3.set_ylim(0, 100)

        # Add percentage labels
        for bar, wr in zip(bars3, wr_values):
            height = bar.get_height()
            ax3.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 1,
                f"{wr:.1f}%",
                ha="center",
                va="bottom",
            )

    # Drake control over time
    game_numbers = range(1, len(drake_data["player_team_drakes"]) + 1)
    ax4.plot(
        game_numbers,
        drake_data["player_team_drakes"],
        "o-",
        label="Player Team",
        color="blue",
        alpha=0.7,
    )
    ax4.plot(
        game_numbers,
        drake_data["enemy_team_drakes"],
        "s-",
        label="Enemy Team",
        color="red",
        alpha=0.7,
    )

    ax4.set_xlabel("Game Number")
    ax4.set_ylabel("Dragons Taken")
    ax4.set_title(f"{player_name} - Drake Control Over Time")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    from stats_visualization.utils import save_figure, sanitize_player

    save_figure(
        fig,
        f"drake_analysis_{sanitize_player(player_name)}",
        description="drake analysis",
    )
    plt.show()


def main():
    """Main function for drake analysis visualization."""
    parser = argparse.ArgumentParser(
        description="Generate personal drake statistics visualization (Summoner's Rift by default – ARAM excluded unless --include-aram)"
    )
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
        "-a",
        "--include-aram",
        action="store_true",
        help="Include ARAM matches (excluded by default).",
    )
    parser.add_argument(
        "-q",
        "--queue",
        type=int,
        nargs="*",
        help="Restrict to specific queue IDs (space separated). Example: --queue 420 440",
    )
    parser.add_argument(
        "-R",
        "--ranked-only",
        action="store_true",
        help="Shortcut for --queue 420 440 (Ranked Solo/Duo + Flex).",
    )
    parser.add_argument(
        "-M",
        "--modes",
        nargs="*",
        help="Whitelist specific gameMode values (e.g. CLASSIC CHERRY).",
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

    print(f"Analyzing drake data for {player_display}...")
    queue_filter = args.queue
    if args.ranked_only:
        queue_filter = [420, 440] if queue_filter is None else queue_filter
    drake_data = extract_drake_data(
        player_puuid,
        matches_dir,
        include_aram=args.include_aram,
        queue_filter=queue_filter,
        game_mode_whitelist=args.modes,
    )

    # Generate visualization
    plot_drake_analysis(player_display, drake_data)


if __name__ == "__main__":
    main()
