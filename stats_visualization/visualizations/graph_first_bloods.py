#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Personal first blood statistics visualization for League of Legends match data.
Analyzes early game performance and first blood statistics from personal match history.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import argparse
import sys
import os

# Load environment variables from config.env if present
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from stats_visualization import league
from stats_visualization import analyze
from stats_visualization.viz_types import EarlyGameData


def extract_early_game_data(
    player_puuid: str, matches_dir: str = "matches"
) -> EarlyGameData:
    """
    Extract early game and first blood data for a specific player from match history.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing early game statistics
    """
    matches = analyze.load_match_files(matches_dir)
    early_game_data: EarlyGameData = {
        "first_blood_kills": 0,
        "first_blood_deaths": 0,
        "first_blood_assists": 0,
        "first_tower_kills": 0,
        "early_kills": [],
        "early_deaths": [],
        "early_cs": [],
        "wins": [],
        "champions": [],
        "roles": [],
        "total_games": 0,
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

        early_game_data["total_games"] += 1

        # First blood statistics
        if player_data.get("firstBloodKill", False):
            early_game_data["first_blood_kills"] += 1
        if player_data.get("firstBloodAssist", False):
            early_game_data["first_blood_assists"] += 1
        if player_data.get("firstBloodVictim", False):
            early_game_data["first_blood_deaths"] += 1

        # First tower
        if player_data.get("firstTowerKill", False):
            early_game_data["first_tower_kills"] += 1

        # Early game performance (first 15 minutes approximation)
        # Using available stats as proxies for early game performance
        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        cs = player_data.get("totalMinionsKilled", 0) + player_data.get(
            "neutralMinionsKilled", 0
        )

        early_game_data["early_kills"].append(kills)
        early_game_data["early_deaths"].append(deaths)
        early_game_data["early_cs"].append(cs)
        early_game_data["wins"].append(player_data.get("win", False))
        early_game_data["champions"].append(player_data.get("championName", "Unknown"))
        early_game_data["roles"].append(player_data.get("teamPosition", "Unknown"))

    return early_game_data


def plot_first_blood_analysis(player_name: str, early_game_data: EarlyGameData) -> None:
    """
    Create first blood and early game analysis visualization.
    """
    if early_game_data["total_games"] == 0:
        print(f"No games found for {player_name}")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # First blood statistics
    fb_categories = [
        "First Blood Kills",
        "First Blood Assists",
        "First Blood Deaths",
        "First Tower Kills",
    ]
    fb_counts = [
        early_game_data["first_blood_kills"],
        early_game_data["first_blood_assists"],
        early_game_data["first_blood_deaths"],
        early_game_data["first_tower_kills"],
    ]
    fb_percentages = [
        count / early_game_data["total_games"] * 100 for count in fb_counts
    ]
    colors = ["green", "blue", "red", "orange"]

    bars1 = ax1.bar(fb_categories, fb_percentages, color=colors, alpha=0.7)
    ax1.set_ylabel("Percentage of Games (%)")
    ax1.set_title(f"{player_name} - First Blood & Early Objectives")
    ax1.set_ylim(0, max(fb_percentages) * 1.2 if fb_percentages else 10)

    # Add percentage and count labels
    for bar, percentage, count in zip(bars1, fb_percentages, fb_counts):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.5,
            f'{percentage:.1f}%\n({count}/{early_game_data["total_games"]})',
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax1.tick_params(axis="x", rotation=45)

    # Early game kill distribution
    ax2.hist(
        early_game_data["early_kills"],
        bins=range(0, max(early_game_data["early_kills"]) + 2),
        alpha=0.7,
        color="red",
        edgecolor="black",
    )
    avg_kills = np.mean(early_game_data["early_kills"])
    ax2.axvline(
        avg_kills, color="blue", linestyle="--", label=f"Average: {avg_kills:.1f}"
    )
    ax2.set_xlabel("Kills per Game")
    ax2.set_ylabel("Number of Games")
    ax2.set_title(f"{player_name} - Kill Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Early game deaths distribution
    ax3.hist(
        early_game_data["early_deaths"],
        bins=range(0, max(early_game_data["early_deaths"]) + 2),
        alpha=0.7,
        color="darkred",
        edgecolor="black",
    )
    avg_deaths = np.mean(early_game_data["early_deaths"])
    ax3.axvline(
        avg_deaths, color="blue", linestyle="--", label=f"Average: {avg_deaths:.1f}"
    )
    ax3.set_xlabel("Deaths per Game")
    ax3.set_ylabel("Number of Games")
    ax3.set_title(f"{player_name} - Death Distribution")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Win rate correlation with first blood involvement
    fb_involved = []
    fb_not_involved = []

    for i, (fb_kill, fb_assist, fb_death, win) in enumerate(
        zip(
            [early_game_data["first_blood_kills"] > 0] * early_game_data["total_games"],
            [early_game_data["first_blood_assists"] > 0]
            * early_game_data["total_games"],
            [early_game_data["first_blood_deaths"] > 0]
            * early_game_data["total_games"],
            early_game_data["wins"],
        )
    ):
        # This is a simplified approach - in reality we'd need per-game first blood data
        # For now, we'll use kill/death ratio as proxy for early game performance
        early_kd = early_game_data["early_kills"][i] / max(
            early_game_data["early_deaths"][i], 1
        )
        if early_kd > 1:
            fb_involved.append(win)
        else:
            fb_not_involved.append(win)

    categories = []
    win_rates = []
    colors_wr = []

    if fb_involved:
        categories.append(f"Good Early Game\n({len(fb_involved)} games)")
        win_rates.append(sum(fb_involved) / len(fb_involved) * 100)
        colors_wr.append("green")

    if fb_not_involved:
        categories.append(f"Poor Early Game\n({len(fb_not_involved)} games)")
        win_rates.append(sum(fb_not_involved) / len(fb_not_involved) * 100)
        colors_wr.append("red")

    if categories:
        bars4 = ax4.bar(categories, win_rates, color=colors_wr, alpha=0.7)
        ax4.set_ylabel("Win Rate (%)")
        ax4.set_title(f"{player_name} - Win Rate by Early Game Performance")
        ax4.set_ylim(0, 100)

        # Add percentage labels
        for bar, wr in zip(bars4, win_rates):
            height = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 1,
                f"{wr:.1f}%",
                ha="center",
                va="bottom",
            )

    plt.tight_layout()
    from stats_visualization.utils import save_figure, sanitize_player

    save_figure(
        fig,
        f"first_bloods_{sanitize_player(player_name)}",
        description="first blood analysis",
    )
    plt.show()


def plot_role_early_game_comparison(
    player_name: str, early_game_data: EarlyGameData
) -> None:
    """
    Compare early game performance across different roles.
    """
    from collections import defaultdict

    role_data = defaultdict(lambda: {"kills": [], "deaths": [], "cs": [], "games": 0})

    for role, kills, deaths, cs in zip(
        early_game_data["roles"],
        early_game_data["early_kills"],
        early_game_data["early_deaths"],
        early_game_data["early_cs"],
    ):
        if role and role != "Unknown":
            role_data[role]["kills"].append(kills)
            role_data[role]["deaths"].append(deaths)
            role_data[role]["cs"].append(cs)
            role_data[role]["games"] += 1

    # Filter roles with at least 2 games
    filtered_roles = {
        role: data for role, data in role_data.items() if data["games"] >= 2
    }

    if not filtered_roles:
        print(f"No roles with enough games for comparison")
        return

    role_names = list(filtered_roles.keys())
    avg_kills = [np.mean(filtered_roles[role]["kills"]) for role in role_names]
    avg_deaths = [np.mean(filtered_roles[role]["deaths"]) for role in role_names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Average kills by role
    bars1 = ax1.bar(role_names, avg_kills, color="lightblue", alpha=0.7)
    ax1.set_ylabel("Average Kills per Game")
    ax1.set_title(f"{player_name} - Average Kills by Role")

    for bar, kills, role in zip(bars1, avg_kills, role_names):
        height = bar.get_height()
        games = filtered_roles[role]["games"]
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.05,
            f"{kills:.1f}\n({games}g)",
            ha="center",
            va="bottom",
        )

    # Average deaths by role
    bars2 = ax2.bar(role_names, avg_deaths, color="lightcoral", alpha=0.7)
    ax2.set_ylabel("Average Deaths per Game")
    ax2.set_title(f"{player_name} - Average Deaths by Role")

    for bar, deaths, role in zip(bars2, avg_deaths, role_names):
        height = bar.get_height()
        games = filtered_roles[role]["games"]
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.05,
            f"{deaths:.1f}\n({games}g)",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    from stats_visualization.utils import save_figure, sanitize_player

    save_figure(
        fig,
        f"role_early_game_{sanitize_player(player_name)}",
        description="early game role comparison",
    )
    plt.show()


def main() -> None:
    """Main function for early game and first blood analysis visualization."""
    parser = argparse.ArgumentParser(
        description="Generate personal early game and first blood statistics visualization"
    )
    parser.add_argument("game_name", type=str, help="Riot game name (e.g. frowtch)")
    parser.add_argument("tag_line", type=str, help="Riot tag line (e.g. blue)")
    parser.add_argument(
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
    parser.add_argument(
        "--role-comparison", action="store_true", help="Show role comparison"
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
    num_matches = league.ensure_matches_for_player(
        player_puuid, token, matches_dir, min_matches=1, fetch_count=10
    )
    if num_matches == 0:
        print(f"Failed to fetch or find any matches for {player_display}.")
        return

    print(f"Analyzing early game data for {player_display}...")
    early_game_data = extract_early_game_data(player_puuid, matches_dir)

    if early_game_data["total_games"] == 0:
        print(f"No matches found for {player_display}")
        return

    plot_first_blood_analysis(player_display, early_game_data)

    if args.role_comparison:
        plot_role_early_game_comparison(player_display, early_game_data)


if __name__ == "__main__":
    main()
