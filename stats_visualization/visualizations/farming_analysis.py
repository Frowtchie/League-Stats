#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Farming and economy analysis visualization module for League of Legends match data.
Analyzes CS per minute, gold efficiency, and economic performance.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import argparse
import sys

# Load environment variables from config.env if present
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
import league
import analyze


def extract_economy_data(
    player_puuid: str, matches_dir: str = "matches"
) -> Dict[str, Any]:
    """
    Extract economy and farming data for a specific player.

    Args:
        player_puuid (str): PUUID of the player
        matches_dir (str): Directory containing match JSON files

    Returns:
        Dict containing economy statistics
    """
    matches = analyze.load_match_files(matches_dir)
    economy_data = {
        "cs_per_min": [],
        "gold_per_min": [],
        "damage_per_gold": [],
        "vision_score": [],
        "game_durations": [],
        "total_cs": [],
        "total_gold": [],
        "total_damage": [],
        "roles": [],
        "champions": [],
        "wins": [],
        "items_purchased": [],
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

        game_duration = match["info"].get("gameDuration", 0)
        if game_duration <= 0:
            continue

        economy_data["total_games"] += 1

        # Basic stats
        total_cs = player_data.get("totalMinionsKilled", 0) + player_data.get(
            "neutralMinionsKilled", 0
        )
        total_gold = player_data.get("goldEarned", 0)
        total_damage = player_data.get("totalDamageDealtToChampions", 0)
        vision_score = player_data.get("visionScore", 0)

        # Calculate per-minute stats
        duration_minutes = game_duration / 60
        cs_per_min = total_cs / duration_minutes if duration_minutes > 0 else 0
        gold_per_min = total_gold / duration_minutes if duration_minutes > 0 else 0
        damage_per_gold = total_damage / total_gold if total_gold > 0 else 0

        # Store data
        economy_data["cs_per_min"].append(cs_per_min)
        economy_data["gold_per_min"].append(gold_per_min)
        economy_data["damage_per_gold"].append(damage_per_gold)
        economy_data["vision_score"].append(vision_score)
        economy_data["game_durations"].append(duration_minutes)
        economy_data["total_cs"].append(total_cs)
        economy_data["total_gold"].append(total_gold)
        economy_data["total_damage"].append(total_damage)
        economy_data["roles"].append(player_data.get("teamPosition", "Unknown"))
        economy_data["champions"].append(player_data.get("championName", "Unknown"))
        economy_data["wins"].append(player_data.get("win", False))

        # Count items purchased (item0 through item6)
        items = [player_data.get(f"item{i}", 0) for i in range(7)]
        items_bought = sum(1 for item in items if item > 0)
        economy_data["items_purchased"].append(items_bought)

    return economy_data


def plot_farming_performance(player_name: str, economy_data: Dict[str, Any]):
    """
    Plot farming performance (CS/min) analysis.
    """
    cs_per_min = economy_data["cs_per_min"]
    roles = economy_data["roles"]
    wins = economy_data["wins"]

    if not cs_per_min:
        print(f"No farming data found for {player_name}")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Overall CS/min distribution
    ax1.hist(cs_per_min, bins=15, alpha=0.7, color="skyblue", edgecolor="black")
    avg_cs = np.mean(cs_per_min)
    ax1.axvline(avg_cs, color="red", linestyle="--", label=f"Average: {avg_cs:.1f}")
    ax1.set_xlabel("CS per Minute")
    ax1.set_ylabel("Number of Games")
    ax1.set_title(f"{player_name} - CS/min Distribution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # CS/min by role
    role_cs = defaultdict(list)
    for cs, role in zip(cs_per_min, roles):
        if role and role != "Unknown":
            role_cs[role].append(cs)

    if role_cs:
        roles_list = list(role_cs.keys())
        cs_by_role = [role_cs[role] for role in roles_list]

        bp = ax2.boxplot(cs_by_role, tick_labels=roles_list, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("lightgreen")
        ax2.set_ylabel("CS per Minute")
        ax2.set_title(f"{player_name} - CS/min by Role")
        ax2.grid(True, alpha=0.3)

    # CS/min over time (game progression)
    game_numbers = range(1, len(cs_per_min) + 1)
    ax3.plot(game_numbers, cs_per_min, "o-", alpha=0.7, color="blue")

    # Add trend line
    if len(cs_per_min) > 1:
        z = np.polyfit(game_numbers, cs_per_min, 1)
        p = np.poly1d(z)
        ax3.plot(
            game_numbers,
            p(game_numbers),
            "r--",
            alpha=0.8,
            label=f"Trend: {z[0]:.2f} CS/min per game",
        )
        ax3.legend()

    ax3.set_xlabel("Game Number")
    ax3.set_ylabel("CS per Minute")
    ax3.set_title(f"{player_name} - CS/min Progression")
    ax3.grid(True, alpha=0.3)

    # Win rate by CS performance
    cs_quartiles = np.percentile(cs_per_min, [25, 50, 75])
    categories = ["Bottom 25%", "25-50%", "50-75%", "Top 25%"]
    win_rates = []

    for i, (lower, upper) in enumerate(
        [
            (0, cs_quartiles[0]),
            (cs_quartiles[0], cs_quartiles[1]),
            (cs_quartiles[1], cs_quartiles[2]),
            (cs_quartiles[2], float("inf")),
        ]
    ):
        games_in_range = [
            (cs, win)
            for cs, win in zip(cs_per_min, wins)
            if lower <= cs < upper or (i == 3 and cs >= lower)
        ]
        if games_in_range:
            wins_in_range = sum(win for cs, win in games_in_range)
            win_rate = wins_in_range / len(games_in_range) * 100
            win_rates.append(win_rate)
        else:
            win_rates.append(0)

    bars = ax4.bar(
        categories, win_rates, color=["red", "orange", "yellow", "green"], alpha=0.7
    )
    ax4.set_ylabel("Win Rate (%)")
    ax4.set_xlabel("CS/min Performance")
    ax4.set_title(f"{player_name} - Win Rate by CS Performance")
    ax4.set_ylim(0, 100)

    # Add value labels
    for bar, wr in zip(bars, win_rates):
        height = bar.get_height()
        ax4.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{wr:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.show()


def plot_gold_efficiency(player_name: str, economy_data: Dict[str, Any]):
    """
    Plot gold efficiency and economy analysis.
    """
    gold_per_min = economy_data["gold_per_min"]
    damage_per_gold = economy_data["damage_per_gold"]
    total_gold = economy_data["total_gold"]
    total_damage = economy_data["total_damage"]

    if not gold_per_min:
        print(f"No economy data found for {player_name}")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # Gold per minute distribution
    ax1.hist(gold_per_min, bins=15, alpha=0.7, color="gold", edgecolor="black")
    avg_gpm = np.mean(gold_per_min)
    ax1.axvline(avg_gpm, color="red", linestyle="--", label=f"Average: {avg_gpm:.0f}")
    ax1.set_xlabel("Gold per Minute")
    ax1.set_ylabel("Number of Games")
    ax1.set_title(f"{player_name} - Gold/min Distribution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Damage per gold efficiency
    ax2.hist(damage_per_gold, bins=15, alpha=0.7, color="orange", edgecolor="black")
    avg_dpg = np.mean(damage_per_gold)
    ax2.axvline(avg_dpg, color="red", linestyle="--", label=f"Average: {avg_dpg:.2f}")
    ax2.set_xlabel("Damage per Gold")
    ax2.set_ylabel("Number of Games")
    ax2.set_title(f"{player_name} - Damage per Gold Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Gold vs Damage scatter plot
    ax3.scatter(total_gold, total_damage, alpha=0.6, color="purple")

    # Add correlation line
    if len(total_gold) > 1:
        correlation = np.corrcoef(total_gold, total_damage)[0, 1]
        z = np.polyfit(total_gold, total_damage, 1)
        p = np.poly1d(z)
        ax3.plot(
            sorted(total_gold),
            p(sorted(total_gold)),
            "r--",
            alpha=0.8,
            label=f"Correlation: {correlation:.3f}",
        )
        ax3.legend()

    ax3.set_xlabel("Total Gold Earned")
    ax3.set_ylabel("Total Damage to Champions")
    ax3.set_title(f"{player_name} - Gold vs Damage Correlation")
    ax3.grid(True, alpha=0.3)

    # Format axes
    ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1000:.0f}K"))
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x/1000:.0f}K"))

    # Economic efficiency over time
    game_numbers = range(1, len(damage_per_gold) + 1)
    ax4.plot(game_numbers, damage_per_gold, "o-", alpha=0.7, color="green")

    # Add trend line
    if len(damage_per_gold) > 1:
        z = np.polyfit(game_numbers, damage_per_gold, 1)
        p = np.poly1d(z)
        ax4.plot(
            game_numbers,
            p(game_numbers),
            "r--",
            alpha=0.8,
            label=f"Trend: {z[0]:.4f} DPG per game",
        )
        ax4.legend()

    ax4.set_xlabel("Game Number")
    ax4.set_ylabel("Damage per Gold")
    ax4.set_title(f"{player_name} - Economic Efficiency Progression")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def plot_role_economy_comparison(player_name: str, economy_data: Dict[str, Any]):
    """
    Compare economic performance across different roles.
    """
    roles = economy_data["roles"]
    cs_per_min = economy_data["cs_per_min"]
    gold_per_min = economy_data["gold_per_min"]
    vision_scores = economy_data["vision_score"]

    # Group data by role
    role_data = defaultdict(
        lambda: {"cs_per_min": [], "gold_per_min": [], "vision_score": [], "games": 0}
    )

    for role, cs, gpm, vision in zip(roles, cs_per_min, gold_per_min, vision_scores):
        if role and role != "Unknown":
            role_data[role]["cs_per_min"].append(cs)
            role_data[role]["gold_per_min"].append(gpm)
            role_data[role]["vision_score"].append(vision)
            role_data[role]["games"] += 1

    if not role_data:
        print(f"No role-specific data found for {player_name}")
        return

    # Filter roles with at least 2 games
    filtered_roles = {
        role: data for role, data in role_data.items() if data["games"] >= 2
    }

    if not filtered_roles:
        print(f"No roles with enough games for {player_name}")
        return

    role_names = list(filtered_roles.keys())
    avg_cs = [np.mean(filtered_roles[role]["cs_per_min"]) for role in role_names]
    avg_gpm = [np.mean(filtered_roles[role]["gold_per_min"]) for role in role_names]
    avg_vision = [np.mean(filtered_roles[role]["vision_score"]) for role in role_names]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

    # CS/min by role
    bars1 = ax1.bar(role_names, avg_cs, color="lightblue", alpha=0.7)
    ax1.set_ylabel("Average CS per Minute")
    ax1.set_title(f"{player_name} - CS/min by Role")
    ax1.set_xlabel("Role")

    # Add value labels and game counts
    for bar, cs, role in zip(bars1, avg_cs, role_names):
        height = bar.get_height()
        games = filtered_roles[role]["games"]
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.2,
            f"{cs:.1f}\n({games}g)",
            ha="center",
            va="bottom",
        )

    # Gold/min by role
    bars2 = ax2.bar(role_names, avg_gpm, color="gold", alpha=0.7)
    ax2.set_ylabel("Average Gold per Minute")
    ax2.set_title(f"{player_name} - Gold/min by Role")
    ax2.set_xlabel("Role")

    for bar, gpm, role in zip(bars2, avg_gpm, role_names):
        height = bar.get_height()
        games = filtered_roles[role]["games"]
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 5,
            f"{gpm:.0f}\n({games}g)",
            ha="center",
            va="bottom",
        )

    # Vision score by role
    bars3 = ax3.bar(role_names, avg_vision, color="purple", alpha=0.7)
    ax3.set_ylabel("Average Vision Score")
    ax3.set_title(f"{player_name} - Vision Score by Role")
    ax3.set_xlabel("Role")

    for bar, vision, role in zip(bars3, avg_vision, role_names):
        height = bar.get_height()
        games = filtered_roles[role]["games"]
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.5,
            f"{vision:.1f}\n({games}g)",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.show()


def main():
    """Main function for farming and economy analysis visualization."""
    parser = argparse.ArgumentParser(
        description="Generate farming and economy analysis visualizations"
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
        choices=["farming", "gold", "roles", "all"],
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

    print(f"Analyzing economy data for {player_display}...")
    economy_data = extract_economy_data(player_puuid, matches_dir)

    # Generate requested charts
    if args.chart == "farming" or args.chart == "all":
        print(f"Generating farming performance chart for {player_display}...")
        plot_farming_performance(player_display, economy_data)

    if args.chart == "gold" or args.chart == "all":
        print(f"Generating gold efficiency chart for {player_display}...")
        plot_gold_efficiency(player_display, economy_data)

    if args.chart == "roles" or args.chart == "all":
        print(f"Generating role economy comparison for {player_display}...")
        plot_role_economy_comparison(player_display, economy_data)


if __name__ == "__main__":
    main()
