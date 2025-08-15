from __future__ import annotations

from typing import TypedDict


class _TrendPoint(TypedDict):
    kda: float
    cumulative_win_rate: float  # percentage 0-100


def plot_performance_trends(
    player_puuid: str, player_name: str, matches_dir: str = "matches"
):
    """Plot KDA and win rate trends over time for a player.

    Uses shared save_figure utility for consistent output handling.
    """
    matches = load_player_match_data(player_puuid, matches_dir)
    if not matches:
        print(f"No matches found for {player_name}")
        return

    # Sort chronologically
    matches.sort(key=lambda x: x.get("info", {}).get("gameCreation", 0))

    trend_points: list[_TrendPoint] = []
    wins = 0
    for idx, match in enumerate(matches):
        participant = next(
            (
                p
                for p in match.get("info", {}).get("participants", [])
                if p.get("puuid") == player_puuid
            ),
            None,
        )
        if not participant:
            continue
        kills = participant.get("kills", 0)
        deaths = participant.get("deaths", 0)
        assists = participant.get("assists", 0)
        kda = (kills + assists) / max(deaths, 1)
        if participant.get("win", False):
            wins += 1
        win_rate = wins / (idx + 1) * 100
        trend_points.append({"kda": kda, "cumulative_win_rate": win_rate})

    if not trend_points:
        print(
            f"No valid data to plot for {player_name}. Debug: matches={len(matches)}, usable=0"
        )
        return

    game_numbers = list(range(1, len(trend_points) + 1))
    kdas = [tp["kda"] for tp in trend_points]
    win_rates = [tp["cumulative_win_rate"] for tp in trend_points]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    # KDA trend
    ax1.plot(game_numbers, kdas, "b-", marker="o", markersize=4, alpha=0.7)
    avg_kda = float(np.mean(kdas))
    ax1.axhline(
        y=avg_kda,
        color="r",
        linestyle="--",
        alpha=0.7,
        label=f"Average KDA: {avg_kda:.2f}",
    )
    ax1.set_xlabel("Game Number")
    ax1.set_ylabel("KDA Ratio")
    ax1.set_title(f"{player_name} - KDA Trend Over Time")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Win rate trend
    ax2.plot(game_numbers, win_rates, "g-", marker="s", markersize=4, alpha=0.7)
    ax2.axhline(y=50, color="gray", linestyle=":", alpha=0.5, label="50% Win Rate")
    ax2.set_xlabel("Game Number")
    ax2.set_ylabel("Win Rate (%)")
    ax2.set_title(f"{player_name} - Win Rate Trend Over Time")
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(0, 100)

    plt.tight_layout()
    save_figure(
        fig,
        f"performance_trends_{sanitize_player(player_name)}",
        description="performance trends chart",
    )
    plt.show()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Personal performance visualization module for League of Legends match data.
Creates charts and graphs for individual player analysis.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import argparse
import sys
import os
import requests

# Load environment variables from config.env if present
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

# Ensure project root is in sys.path for module imports
import pathlib

project_root = pathlib.Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from stats_visualization import league
from stats_visualization import analyze
from stats_visualization.utils import save_figure, sanitize_player


def load_player_match_data(
    player_puuid: str, matches_dir: str = "matches"
) -> list[dict[str, Any]]:
    """
    Load match data for a specific player.
    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files
    Returns:
        list[dict]: List of match data for the player
    """
    matches: list[dict[str, Any]] = analyze.load_match_files(matches_dir)  # type: ignore[assignment]
    player_matches: list[dict[str, Any]] = []
    for match in matches:
        if "info" not in match or "participants" not in match["info"]:
            continue
        # Check if player participated in this match
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_matches.append(match)
                break
    return player_matches


def plot_champion_performance(
    player_puuid: str, player_name: str, matches_dir: str = "matches"
):
    """
    Plot performance statistics by champion.
    """
    matches = load_player_match_data(player_puuid, matches_dir)

    if not matches:
        print(f"No matches found for {player_name}")
        return

    champion_stats = {}

    for match in matches:
        # Find player data in this match
        player_data = None
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_data = participant
                break

        if not player_data:
            continue

        champion = player_data.get("championName", "Unknown")

        if champion not in champion_stats:
            champion_stats[champion] = {
                "games": 0,
                "wins": 0,
                "total_kda": 0,
                "total_damage": 0,
                "total_gold": 0,
            }

        stats = champion_stats[champion]
        stats["games"] += 1

        if player_data.get("win", False):
            stats["wins"] += 1

        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        kda = (kills + assists) / max(deaths, 1)

        stats["total_kda"] += kda
        stats["total_damage"] += player_data.get("totalDamageDealtToChampions", 0)
        stats["total_gold"] += player_data.get("goldEarned", 0)

    # Filter champions with at least 2 games and get top 8
    filtered_champions = {
        champ: stats for champ, stats in champion_stats.items() if stats["games"] >= 2
    }

    if not filtered_champions:
        print(f"No champions with enough games for {player_name}")
        return

    # Sort by games played and take top 8
    top_champions = dict(
        sorted(filtered_champions.items(), key=lambda x: x[1]["games"], reverse=True)[
            :8
        ]
    )

    champions = list(top_champions.keys())
    win_rates = [
        stats["wins"] / stats["games"] * 100 for stats in top_champions.values()
    ]
    avg_kdas = [stats["total_kda"] / stats["games"] for stats in top_champions.values()]
    games_played = [stats["games"] for stats in top_champions.values()]

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    bars1 = ax1.bar(champions, win_rates, color="skyblue", alpha=0.8)
    ax1.set_ylabel("Win Rate (%)")
    ax1.set_title(f"{player_name} - Win Rate by Champion")
    ax1.set_ylim(0, 100)
    for bar, games in zip(bars1, games_played):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{games}g",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax1.axhline(y=50, color="red", linestyle="--", alpha=0.7, label="50% Win Rate")
    ax1.legend()

    # Plot Average KDA by Champion
    bars2 = ax2.bar(champions, avg_kdas, color="orange", alpha=0.8)
    ax2.set_ylabel("Average KDA")
    ax2.set_title(f"{player_name} - Average KDA by Champion")
    ax2.set_xlabel("Champion")

    plt.tight_layout()
    save_figure(
        fig,
        f"champion_performance_{sanitize_player(player_name)}",
        description="champion performance chart",
    )
    plt.show()


def plot_role_performance(
    player_puuid: str, player_name: str, matches_dir: str = "matches"
):
    """
    Plot performance statistics by role/position.
    """
    matches = load_player_match_data(player_puuid, matches_dir)

    role_stats = {}

    for match in matches:
        # Find player data in this match
        player_data = None
        for participant in match["info"]["participants"]:
            if participant.get("puuid") == player_puuid:
                player_data = participant
                break

        if not player_data:
            continue

        role = player_data.get("teamPosition", "Unknown")
        if role == "":
            role = "Unknown"

        if role not in role_stats:
            role_stats[role] = {
                "games": 0,
                "wins": 0,
                "total_kda": 0,
                "total_damage": 0,
                "total_gold": 0,
            }

        stats = role_stats[role]
        stats["games"] += 1

        if player_data.get("win", False):
            stats["wins"] += 1

        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        kda = (kills + assists) / max(deaths, 1)

        stats["total_kda"] += kda
        stats["total_damage"] += player_data.get("totalDamageDealtToChampions", 0)
        stats["total_gold"] += player_data.get("goldEarned", 0)

    # Filter roles with at least 1 game
    filtered_roles = {
        role: stats for role, stats in role_stats.items() if stats["games"] >= 1
    }

    if not filtered_roles:
        print(f"No role data found for {player_name}")
        return

    roles = list(filtered_roles.keys())
    win_rates = [
        stats["wins"] / stats["games"] * 100 for stats in filtered_roles.values()
    ]
    avg_kdas = [
        stats["total_kda"] / stats["games"] for stats in filtered_roles.values()
    ]
    games_played = [stats["games"] for stats in filtered_roles.values()]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    # Games distribution pie chart
    ax1.pie(games_played, labels=roles, autopct="%1.1f%%", startangle=90)
    ax1.set_title(f"{player_name} - Games by Role")

    # Win rate by role
    bars2 = ax2.bar(roles, win_rates, color="lightgreen", alpha=0.7)
    ax2.axhline(y=50, color="red", linestyle="--", alpha=0.7, label="50% Win Rate")
    ax2.set_ylabel("Win Rate (%)")
    ax2.set_title("Win Rate by Role")
    ax2.legend()
    ax2.set_ylim(0, 100)

    # Add game count labels
    for bar, games in zip(bars2, games_played):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{games}g",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Average KDA by role
    ax3.bar(roles, avg_kdas, color="orange", alpha=0.7)
    ax3.set_ylabel("Average KDA")
    ax3.set_title("Average KDA by Role")
    ax3.set_xlabel("Role")

    # Average damage by role
    avg_damages = [
        stats["total_damage"] / stats["games"] for stats in filtered_roles.values()
    ]
    ax4.bar(roles, avg_damages, color="purple", alpha=0.7)
    ax4.set_ylabel("Average Damage to Champions")
    ax4.set_title("Average Damage by Role")
    ax4.set_xlabel("Role")

    # Format damage values
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1000:.0f}K"))

    plt.tight_layout()
    save_figure(
        fig,
        f"role_performance_{sanitize_player(player_name)}",
        description="role performance chart",
    )
    plt.show()


def fetch_puuid_by_riot_id(game_name: str, tag_line: str, token: str) -> str:
    """
    Fetch PUUID for a player using their Riot ID (game name + tag line).
    """
    base_url = "https://americas.api.riotgames.com"
    url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": token}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "puuid" not in data:
            raise ValueError("Invalid response format - missing PUUID")
        return data["puuid"]
    except Exception as e:
        print(f"Error fetching PUUID for {game_name}#{tag_line}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Generate personal performance visualizations"
    )
    parser.add_argument(
        "game_name", type=str, help="The player's game name (e.g., Frowtch)"
    )
    parser.add_argument("tag_line", type=str, help="The player's tag line (e.g., blue)")
    parser.add_argument(
        "--matches-dir",
        type=str,
        default="matches",
        help="Directory containing match JSON files",
    )
    parser.add_argument(
        "--chart",
        type=str,
        choices=["trends", "champions", "roles", "all"],
        default="all",
        help="Type of chart to generate",
    )

    args = parser.parse_args()

    # Get API token
    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        print("RIOT_API_TOKEN environment variable is not set.")
        return

    # Try config first
    puuids = league.load_player_config()
    player_key = args.game_name
    player_puuid = puuids.get(player_key)
    player_display = f"{args.game_name}#{args.tag_line}"

    if not player_puuid:
        try:
            player_puuid = fetch_puuid_by_riot_id(args.game_name, args.tag_line, token)
            print(f"Fetched PUUID for {player_display}")
        except Exception:
            print(
                f"Player '{player_display}' not found in config and could not fetch from Riot API."
            )
            return

    matches_dir = args.matches_dir
    # Ensure there are matches for this player, fetch if needed
    num_matches = league.ensure_matches_for_player(
        player_puuid, token, matches_dir, min_matches=1, fetch_count=20
    )
    if num_matches == 0:
        print(f"Failed to fetch or find any matches for {player_display}.")
        return

    # Generate requested charts
    if args.chart == "trends" or args.chart == "all":
        print(f"Generating performance trends for {player_display}...")
        plot_performance_trends(player_puuid, player_display, matches_dir)

    if args.chart == "champions" or args.chart == "all":
        print(f"Generating champion performance for {player_display}...")
        plot_champion_performance(player_puuid, player_display, matches_dir)

    if args.chart == "roles" or args.chart == "all":
        print(f"Generating role performance for {player_display}...")
        plot_role_performance(player_puuid, player_display, matches_dir)


if __name__ == "__main__":
    main()
