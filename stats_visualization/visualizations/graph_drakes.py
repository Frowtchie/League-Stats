#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Drake statistics visualization.

Focuses on extracting minimal typed data from raw match JSON while keeping
implementation simple (avoid over-defensive runtime checks that confuse
static analysis). Only keys actually used are typed via small TypedDicts.
"""
from __future__ import annotations
import os
import sys
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Any, Dict, TypedDict, cast
from dotenv import load_dotenv
from stats_visualization import league, analyze
from stats_visualization.viz_types import DrakeData
from stats_visualization.utils import filter_matches, save_figure, sanitize_player

sys.path.append(str(Path(__file__).parent.parent.parent))  # noqa: E402
load_dotenv(dotenv_path="config.env")


class _Participant(TypedDict, total=False):
    puuid: str
    teamId: int
    win: bool


class _DragonObj(TypedDict, total=False):
    kills: int


class _Objectives(TypedDict, total=False):
    dragon: _DragonObj


class _Team(TypedDict, total=False):
    teamId: int
    objectives: _Objectives


def extract_drake_data(
    player_puuid: str,
    matches_dir: str = "matches",
    include_aram: bool = False,
    queue_filter: Optional[List[int]] = None,
    game_mode_whitelist: Optional[List[str]] = None,
) -> DrakeData:
    """Extract drake-related data for a specific player from match history."""
    raw_matches = analyze.load_match_files(matches_dir)
    matches = filter_matches(
        raw_matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )
    drake_data: DrakeData = {
        "player_team_drakes": [],
        "enemy_team_drakes": [],
        "wins": [],
        "game_durations": [],
        "total_games": 0,
    }

    for match in matches:
        info_raw = match.get("info")
        if not isinstance(info_raw, dict):
            continue
        participants_raw = info_raw.get("participants")
        if not isinstance(participants_raw, list):
            continue
        participants: List[_Participant] = [
            cast(_Participant, p) for p in participants_raw if isinstance(p, dict)
        ]
        player_team_id: Optional[int] = None
        player_won = False
        for part in participants:
            if part.get("puuid") == player_puuid:
                tid_val = part.get("teamId")
                if isinstance(tid_val, int):
                    player_team_id = tid_val
                player_won = bool(part.get("win", False))
                break
        if player_team_id is None:
            continue
        drake_data["total_games"] += 1
        gdur = info_raw.get("gameDuration")
        if isinstance(gdur, (int, float)):
            drake_data["game_durations"].append(float(gdur) / 60.0)
        else:
            drake_data["game_durations"].append(0.0)
        drake_data["wins"].append(player_won)
        teams_raw = info_raw.get("teams")
        if isinstance(teams_raw, list):
            teams: List[_Team] = [cast(_Team, t) for t in teams_raw if isinstance(t, dict)]
            player_drakes = 0
            enemy_drakes = 0
            for team in teams:
                obj = team.get("objectives", {})
                if isinstance(obj, dict):
                    dragon = obj.get("dragon", {})
                    if isinstance(dragon, dict):
                        dk = dragon.get("kills", 0)
                        if isinstance(dk, int):
                            if team.get("teamId") == player_team_id:
                                player_drakes = dk
                            else:
                                enemy_drakes = dk
            drake_data["player_team_drakes"].append(player_drakes)
            drake_data["enemy_team_drakes"].append(enemy_drakes)
    return drake_data


def plot_drake_analysis(player_name: str, drake_data: DrakeData) -> None:
    """Create comprehensive drake analysis visualization."""
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
    team_colors = ["lightblue", "lightcoral"]

    bars1 = ax1.bar(teams, avg_drakes, color=team_colors, alpha=0.7)
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
    win_rates: dict[str, list[bool]] = {"Behind": [], "Even": [], "Ahead": []}
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

    categories: list[str] = []
    wr_values: list[float] = []
    colors: list[str] = []

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

    save_figure(
        fig,
        f"drake_analysis_{sanitize_player(player_name)}",
        description="drake analysis",
    )
    plt.show()


def main():
    """Main function for drake analysis visualization."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate personal drake statistics visualization (SR default – ARAM excluded "
            "unless --include-aram)"
        )
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
    num_matches = league.ensure_matches_for_player(
        player_puuid, token, matches_dir, min_matches=1, fetch_count=10
    )
    if num_matches == 0:
        print(f"Failed to fetch or find any matches for {player_display}.")
        return

    if not args.no_clean_output:
        from stats_visualization.utils import clean_output

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
