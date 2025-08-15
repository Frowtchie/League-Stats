#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Objective analysis visualization module for League of Legends match data.
Analyzes and visualizes objective control and game impact for personal matches.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict

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
from stats_visualization.viz_types import ObjectiveData


def extract_objective_data(
    player_puuid: str, matches_dir: str = "matches"
) -> ObjectiveData:
    """
    Extract objective-related data for a specific player.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing objective statistics
    """
    matches = analyze.load_match_files(matches_dir)
    objective_data: ObjectiveData = {
        "dragons": {"player_team": [], "enemy_team": [], "wins": [], "types": []},
        "barons": {"player_team": [], "enemy_team": [], "wins": [], "types": []},
        "heralds": {"player_team": [], "enemy_team": [], "wins": [], "types": []},
        "towers": {"player_team": [], "enemy_team": [], "wins": [], "types": []},
        "first_objectives": {
            "dragon": 0,
            "baron": 0,
            "herald": 0,
            "tower": 0,
            "blood": 0,
        },
        "total_games": 0,
    }

    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue

        # Find player's team ID
        player_team_id = None
        player_won = False

        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_team_id = participant.get("teamId")
                player_won = participant.get("win", False)
                break

        if player_team_id is None:
            continue

        objective_data["total_games"] += 1

        # Extract team objectives
        if "teams" in match["info"]:
            player_team_objectives = None
            enemy_team_objectives = None

            for team in match["info"]["teams"]:
                if team["teamId"] == player_team_id:
                    player_team_objectives = team.get("objectives", {})
                else:
                    enemy_team_objectives = team.get("objectives", {})

            if player_team_objectives and enemy_team_objectives:
                # Dragons
                player_dragons = player_team_objectives.get("dragon", {}).get(
                    "kills", 0
                )
                enemy_dragons = enemy_team_objectives.get("dragon", {}).get("kills", 0)
                objective_data["dragons"]["player_team"].append(player_dragons)
                objective_data["dragons"]["enemy_team"].append(enemy_dragons)
                objective_data["dragons"]["wins"].append(player_won)

                # Barons
                player_barons = player_team_objectives.get("baron", {}).get("kills", 0)
                enemy_barons = enemy_team_objectives.get("baron", {}).get("kills", 0)
                objective_data["barons"]["player_team"].append(player_barons)
                objective_data["barons"]["enemy_team"].append(enemy_barons)
                objective_data["barons"]["wins"].append(player_won)

                # Rift Heralds
                player_heralds = player_team_objectives.get("riftHerald", {}).get(
                    "kills", 0
                )
                enemy_heralds = enemy_team_objectives.get("riftHerald", {}).get(
                    "kills", 0
                )
                objective_data["heralds"]["player_team"].append(player_heralds)
                objective_data["heralds"]["enemy_team"].append(enemy_heralds)
                objective_data["heralds"]["wins"].append(player_won)

                # Towers
                player_towers = player_team_objectives.get("tower", {}).get("kills", 0)
                enemy_towers = enemy_team_objectives.get("tower", {}).get("kills", 0)
                objective_data["towers"]["player_team"].append(player_towers)
                objective_data["towers"]["enemy_team"].append(enemy_towers)
                objective_data["towers"]["wins"].append(player_won)

                # First objectives
                if player_team_objectives.get("dragon", {}).get("first", False):
                    objective_data["first_objectives"]["dragon"] += 1
                if player_team_objectives.get("baron", {}).get("first", False):
                    objective_data["first_objectives"]["baron"] += 1
                if player_team_objectives.get("riftHerald", {}).get("first", False):
                    objective_data["first_objectives"]["herald"] += 1
                if player_team_objectives.get("tower", {}).get("first", False):
                    objective_data["first_objectives"]["tower"] += 1

    return objective_data


def plot_objective_control(player_name: str, objective_data: ObjectiveData) -> None:
    """
    Plot objective control statistics.
    """
    objectives = ["Dragons", "Barons", "Heralds", "Towers"]
    data_keys = ["dragons", "barons", "heralds", "towers"]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    axes = [ax1, ax2, ax3, ax4]

    for i, (obj_name, data_key) in enumerate(zip(objectives, data_keys)):
        ax = axes[i]

        player_objs = objective_data[data_key]["player_team"]
        enemy_objs = objective_data[data_key]["enemy_team"]

        if not player_objs:
            ax.text(
                0.5,
                0.5,
                f"No {obj_name.lower()} data",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
            ax.set_title(f"{player_name} - {obj_name} Control")
            continue

        # Calculate averages
        avg_player = np.mean(player_objs)
        avg_enemy = np.mean(enemy_objs)

        # Create comparison bar chart
        categories = ["Player Team", "Enemy Team"]
        values = [avg_player, avg_enemy]
        colors = ["lightblue", "lightcoral"]

        bars = ax.bar(categories, values, color=colors, alpha=0.7)
        ax.set_ylabel(f"Average {obj_name} per Game")
        ax.set_title(f"{player_name} - Average {obj_name} Control")

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.01,
                f"{value:.1f}",
                ha="center",
                va="bottom",
            )

        # Add win rate when ahead in this objective
        wins_when_ahead = sum(
            1
            for p, e, w in zip(
                player_objs, enemy_objs, objective_data[data_key]["wins"]
            )
            if p > e and w
        )
        games_ahead = sum(1 for p, e in zip(player_objs, enemy_objs) if p > e)

        if games_ahead > 0:
            win_rate_ahead = wins_when_ahead / games_ahead * 100
            ax.text(
                0.02,
                0.98,
                f"Win rate when ahead: {win_rate_ahead:.1f}%",
                transform=ax.transAxes,
                va="top",
                ha="left",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
            )

    plt.tight_layout()
    from stats_visualization.utils import save_figure, sanitize_player

    save_figure(
        fig,
        f"objective_control_{sanitize_player(player_name)}",
        description="objective control chart",
    )
    plt.show()


def plot_first_objectives(player_name: str, objective_data: ObjectiveData) -> None:
    """
    Plot first objective statistics.
    """
    first_objs = objective_data["first_objectives"]
    total_games = objective_data["total_games"]

    if total_games == 0:
        print(f"No games found for {player_name}")
        return

    # Calculate percentages
    obj_names = ["First Dragon", "First Baron", "First Herald", "First Tower"]
    obj_keys = ["dragon", "baron", "herald", "tower"]
    percentages = [first_objs[key] / total_games * 100 for key in obj_keys]

    # Create bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        obj_names, percentages, color=["red", "purple", "orange", "gray"], alpha=0.7
    )

    ax.set_ylabel("Success Rate (%)")
    ax.set_title(f"{player_name} - First Objective Success Rate")
    ax.set_ylim(0, 100)

    # Add percentage labels on bars
    for bar, percentage, count in zip(
        bars, percentages, [first_objs[key] for key in obj_keys]
    ):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{percentage:.1f}%\n({count}/{total_games})",
            ha="center",
            va="bottom",
        )

    # Add reference line at 50%
    ax.axhline(y=50, color="black", linestyle="--", alpha=0.5, label="50% Reference")
    ax.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()
    from stats_visualization.utils import save_figure, sanitize_player

    save_figure(
        fig,
        f"first_objectives_{sanitize_player(player_name)}",
        description="first objectives chart",
    )
    plt.show()


def plot_objective_win_correlation(
    player_name: str, objective_data: ObjectiveData
) -> None:
    """
    Plot correlation between objective control and winning.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    objectives = ["Dragons", "Barons", "Heralds", "Towers"]
    data_keys = ["dragons", "barons", "heralds", "towers"]

    win_rates_ahead = []
    win_rates_behind = []
    win_rates_even = []

    for data_key in data_keys:
        player_objs = objective_data[data_key]["player_team"]
        enemy_objs = objective_data[data_key]["enemy_team"]
        wins = objective_data[data_key]["wins"]

        if not player_objs:
            win_rates_ahead.append(0)
            win_rates_behind.append(0)
            win_rates_even.append(0)
            continue

        # Calculate win rates based on objective control
        wins_ahead = sum(
            1 for p, e, w in zip(player_objs, enemy_objs, wins) if p > e and w
        )
        games_ahead = sum(1 for p, e in zip(player_objs, enemy_objs) if p > e)

        wins_behind = sum(
            1 for p, e, w in zip(player_objs, enemy_objs, wins) if p < e and w
        )
        games_behind = sum(1 for p, e in zip(player_objs, enemy_objs) if p < e)

        wins_even = sum(
            1 for p, e, w in zip(player_objs, enemy_objs, wins) if p == e and w
        )
        games_even = sum(1 for p, e in zip(player_objs, enemy_objs) if p == e)

        win_rates_ahead.append(wins_ahead / max(games_ahead, 1) * 100)
        win_rates_behind.append(wins_behind / max(games_behind, 1) * 100)
        win_rates_even.append(wins_even / max(games_even, 1) * 100)

    x = np.arange(len(objectives))
    width = 0.25

    bars1 = ax.bar(
        x - width, win_rates_ahead, width, label="When Ahead", color="green", alpha=0.7
    )
    bars2 = ax.bar(
        x, win_rates_even, width, label="When Even", color="yellow", alpha=0.7
    )
    bars3 = ax.bar(
        x + width, win_rates_behind, width, label="When Behind", color="red", alpha=0.7
    )

    ax.set_ylabel("Win Rate (%)")
    ax.set_xlabel("Objectives")
    ax.set_title(f"{player_name} - Win Rate by Objective Control")
    ax.set_xticks(x)
    ax.set_xticklabels(objectives)
    ax.legend()
    ax.set_ylim(0, 100)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 1,
                    f"{height:.0f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    plt.tight_layout()
    plt.show()


def main():
    """Main function for objective analysis visualization."""

    parser = argparse.ArgumentParser(
        description="Generate objective analysis visualizations"
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
        "--chart",
        type=str,
        choices=["control", "first", "correlation", "all"],
        default="all",
        help="Type of chart to generate",
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

    print(f"Analyzing objective data for {player_display}...")
    objective_data = extract_objective_data(player_puuid, matches_dir)

    # Generate requested charts
    if args.chart == "control" or args.chart == "all":
        print(f"Generating objective control chart for {player_display}...")
        plot_objective_control(player_display, objective_data)

    if args.chart == "first" or args.chart == "all":
        print(f"Generating first objectives chart for {player_display}...")
        plot_first_objectives(player_display, objective_data)

    if args.chart == "correlation" or args.chart == "all":
        print(f"Generating objective-win correlation chart for {player_display}...")
        plot_objective_win_correlation(player_display, objective_data)


if __name__ == "__main__":
    main()
