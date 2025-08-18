#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lane phase CS difference timeline visualization.

Tracks lane phase performance using CS@10, CS@15 and opponent CS
differences.

Opponent inference heuristic:
    - Identify lane via ``teamPosition`` (TOP, JUNGLE, MIDDLE, BOTTOM,
        UTILITY)
    - Find opposing team participant with same lane first.
    - Future: infer via early lane presence from positional timeline.

Diff sign convention::

        diff = player_cs - opponent_cs  # positive => player ahead

Output PNG: ``lane_cs_diff_<player>.png``

Planned (not yet implemented): XP diff, gold diff, percentile shading.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterable, cast
import sys
import logging

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from stats_visualization import analyze
from stats_visualization.utils import (
    filter_matches,
    save_figure,
    sanitize_player,
)
from stats_visualization.viz_types import LaneCSDiffData

logger = logging.getLogger(__name__)

# Ensure project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


LANE_POSITIONS = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}

# Minutes we derive snapshot metrics for
SNAP_MINUTES = (10, 15)


def _infer_opponent(
    player_part: Dict[str, Any], participants: Iterable[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Infer lane opponent based on matching teamPosition on opposing team.

    Returns first participant satisfying heuristic or None.
    """
    player_team = player_part.get("teamId")
    lane = player_part.get("teamPosition")
    if not lane or lane not in LANE_POSITIONS:
        return None
    for p in participants:
        if p.get("teamId") != player_team and p.get("teamPosition") == lane:
            return p
    return None


def _extract_snapshots_from_root_timeline(
    match: Dict[str, Any], participant_ids: List[int]
) -> Dict[int, Dict[int, Dict[str, int]]]:
    """Return snapshots[min][pid] = {cs,xp,gold} via root timeline.

    We walk ``match['timeline']['info']['frames']``. Each frame's
    ``participantFrames`` has cumulative minionsKilled,
    jungleMinionsKilled, xp and totalGold/currentGold. We select the
    frame closest to the target minute timestamp (minute*60*1000).
    """
    timeline_obj = match.get("timeline")
    if not isinstance(timeline_obj, dict):
        return {}
    info_obj = timeline_obj.get("info")
    if not isinstance(info_obj, dict):
        return {}
    frames_raw = info_obj.get("frames")
    if not isinstance(frames_raw, list):
        return {}
    frames: List[Dict[str, Any]] = [cast(Dict[str, Any], f)
                                    for f in frames_raw
                                    if isinstance(f, dict)]
    result: Dict[int, Dict[int, Dict[str, int]]] = {
        m: {} for m in SNAP_MINUTES
    }
    for minute in SNAP_MINUTES:
        target_ms = minute * 60_000
        best: Dict[int, Dict[str, int]] = {}
        # track smallest delta per participant
        deltas: Dict[int, int] = {}
        for frame in frames:
            ts = frame.get("timestamp")
            if not isinstance(ts, (int, float)):
                continue
            delta = abs(int(ts) - target_ms)
            p_frames = frame.get("participantFrames")
            if not isinstance(p_frames, dict):
                continue
            for pid_str, pf_raw in p_frames.items():
                if not isinstance(pf_raw, dict):
                    continue
                try:
                    pid = int(pid_str)
                except (ValueError, TypeError):
                    continue
                if pid not in participant_ids:
                    continue
                prev_delta = deltas.get(pid, 10**12)
                if delta < prev_delta:
                    # Coerce values that may be absent or wrong type
                    mk = pf_raw.get("minionsKilled")
                    jmk = pf_raw.get("jungleMinionsKilled")
                    xp_raw = pf_raw.get("xp")
                    gold_primary = pf_raw.get(
                        "totalGold", pf_raw.get("currentGold")
                    )
                    if not isinstance(mk, (int, float)):
                        mk = 0
                    if not isinstance(jmk, (int, float)):
                        jmk = 0
                    if not isinstance(xp_raw, (int, float)):
                        xp_raw = 0
                    if not isinstance(gold_primary, (int, float)):
                        gold_primary = 0
                    cs = int(mk) + int(jmk)
                    xp = int(xp_raw)
                    gold = int(gold_primary)
                    best[pid] = {"cs": cs, "xp": xp, "gold": gold}
                    deltas[pid] = delta
        result[minute] = best
    return result


def extract_lane_cs_diff_data(
    player_puuid: str,
    matches_dir: str = "matches",
    include_aram: bool = False,
    queue_filter: Optional[List[int]] = None,
    game_mode_whitelist: Optional[List[str]] = None,
) -> LaneCSDiffData:
    """Extract lane CS diff timeline data for player.

    Matches lacking opponent or required timeline data are counted as skipped.
    """
    raw_matches = analyze.load_match_files(matches_dir)
    matches = filter_matches(
        raw_matches,
        include_aram=include_aram,
        allowed_queue_ids=queue_filter,
        allowed_game_modes=game_mode_whitelist,
    )
    data: LaneCSDiffData = {
        "match_indices": [],
        "cs10": [],
        "cs15": [],
        "xp10": [],
        "xp15": [],
        "gold10": [],
        "gold15": [],
        "diff10": [],
        "diff15": [],
        "xp_diff10": [],
        "xp_diff15": [],
        "gold_diff10": [],
        "gold_diff15": [],
        "opponent_missing": 0,
        "total_considered": 0,
    }

    for match in sorted(
        matches,
        key=lambda m: m.get("info", {}).get("gameCreation", 0),
    ):
        info_obj = match.get("info")
        if not isinstance(info_obj, dict):
            continue
        parts_raw = info_obj.get("participants")
        if not isinstance(parts_raw, list):
            continue
        parts: List[Dict[str, Any]] = [
            cast(Dict[str, Any], p) for p in parts_raw if isinstance(p, dict)
        ]
        player_part: Optional[Dict[str, Any]] = None
        for p in parts:
            if p.get("puuid") == player_puuid:
                player_part = p
                break
        if not player_part:
            continue
        data["total_considered"] += 1
        opponent = _infer_opponent(player_part, parts)
        if not opponent:
            data["opponent_missing"] += 1
            logger.debug(
                "Skipping match %s: no opponent inferred",
                match.get("metadata", {}).get("matchId"),
            )
            continue

        player_pid = player_part.get("participantId")
        opp_pid = opponent.get("participantId")
        if not isinstance(player_pid, int) or not isinstance(opp_pid, int):
            data["opponent_missing"] += 1
            continue

        snapshots = _extract_snapshots_from_root_timeline(
            match, [player_pid, opp_pid]
        )
        snap_player: Dict[int, Dict[str, int]] = {}
        snap_opp: Dict[int, Dict[str, int]] = {}
        for minute, pdata in snapshots.items():
            if player_pid in pdata and opp_pid in pdata:
                snap_player[minute] = pdata[player_pid]
                snap_opp[minute] = pdata[opp_pid]

        if not all(m in snap_player and m in snap_opp for m in SNAP_MINUTES):
            data["opponent_missing"] += 1
            continue

        cs10_p = snap_player[10]["cs"]
        cs15_p = snap_player[15]["cs"]
        cs10_o = snap_opp[10]["cs"]
        cs15_o = snap_opp[15]["cs"]
        xp10_p = snap_player[10]["xp"]
        xp15_p = snap_player[15]["xp"]
        xp10_o = snap_opp[10]["xp"]
        xp15_o = snap_opp[15]["xp"]
        gold10_p = snap_player[10]["gold"]
        gold15_p = snap_player[15]["gold"]
        gold10_o = snap_opp[10]["gold"]
        gold15_o = snap_opp[15]["gold"]
        data["match_indices"].append(len(data["match_indices"]) + 1)
        data["cs10"].append(cs10_p)
        data["cs15"].append(cs15_p)
        data["diff10"].append(cs10_p - cs10_o)
        data["diff15"].append(cs15_p - cs15_o)
        data["xp10"].append(xp10_p)
        data["xp15"].append(xp15_p)
        data["gold10"].append(gold10_p)
        data["gold15"].append(gold15_p)
        data["xp_diff10"].append(xp10_p - xp10_o)
        data["xp_diff15"].append(xp15_p - xp15_o)
        data["gold_diff10"].append(gold10_p - gold10_o)
        data["gold_diff15"].append(gold15_p - gold15_o)

    return data


def plot_lane_cs_diff(player_label: str, data: LaneCSDiffData) -> None:
    """Render two figures: (1) CS diffs, (2) XP & Gold diffs (if present)."""
    if not data["match_indices"]:
        print(f"No lane phase CS diff data for {player_label}")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title(f"No lane phase CS diff data for {player_label}")
        save_figure(
            fig,
            f"lane_cs_diff_{sanitize_player(player_label)}",
            description="lane cs diff (empty)",
        )
        plt.close(fig)
        return

    x = data["match_indices"]

    # Figure 1: CS diff timeline
    fig_cs, ax_cs = plt.subplots(figsize=(10, 5))
    ax_cs.plot(
        x,
        data["diff10"],
        marker="o",
        label="CS Δ@10",
        color="#1f77b4",
    )
    ax_cs.plot(
        x,
        data["diff15"],
        marker="s",
        label="CS Δ@15",
        color="#ff7f0e",
    )
    if len(x) > 1:
        z10 = np.polyfit(x, data["diff10"], 1)
        z15 = np.polyfit(x, data["diff15"], 1)
        ax_cs.plot(
            x,
            np.poly1d(z10)(x),
            "--",
            color="#1f77b4",
            alpha=0.5,
        )
        ax_cs.plot(
            x,
            np.poly1d(z15)(x),
            "--",
            color="#ff7f0e",
            alpha=0.5,
        )
    ax_cs.axhline(0, color="black", linewidth=1)
    ax_cs.set_xlabel("Match Index (chronological)")
    ax_cs.set_ylabel("CS Diff (player - opp)")
    ax_cs.set_title(
        f"{player_label} Lane Phase CS Diff (Positive = Ahead)"
    )
    # Legend outside bottom to avoid covering data
    handles_cs, labels_cs = ax_cs.get_legend_handles_labels()
    # Add trend line legends
    handles_cs.append(
        Line2D([0], [0], linestyle="--", color="#1f77b4", alpha=0.5)
    )
    labels_cs.append("Trend CS Δ@10")
    handles_cs.append(
        Line2D([0], [0], linestyle="--", color="#ff7f0e", alpha=0.5)
    )
    labels_cs.append("Trend CS Δ@15")
    ax_cs.legend(
        handles_cs,
        labels_cs,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=len(handles_cs),
    )
    ax_cs.grid(alpha=0.3)
    mean10 = np.mean(data["diff10"]) if data["diff10"] else 0
    mean15 = np.mean(data["diff15"]) if data["diff15"] else 0
    cs_text = (
        f"Games: {len(x)}\nSkipped: {data['opponent_missing']}\n"
        f"Mean CS Δ@10: {mean10:.1f}\nMean CS Δ@15: {mean15:.1f}"
    )
    # Move stats box outside plotting area (top-left margin)
    fig_cs.subplots_adjust(top=0.80)  # space above axes
    fig_cs.text(
        0.01,
        0.985,
        cs_text,
        va="top",
        ha="left",
        fontsize=10,
        bbox=dict(
            boxstyle="round", facecolor="white", alpha=0.85, edgecolor="#999"
        ),
    )
    save_figure(
        fig_cs,
        f"lane_cs_diff_{sanitize_player(player_label)}",
        description="lane cs diff timeline",
    )
    plt.close(fig_cs)

    # Initialize fig_rg to avoid unbound variable errors
    fig_rg = None

    # Figure 2: XP & Gold diff timeline (if any data)
    if data["xp_diff10"] or data["gold_diff10"]:
        fig_rg, ax_rg = plt.subplots(figsize=(10, 5))
        if data["xp_diff10"]:
            ax_rg.plot(
                x,
                data["xp_diff10"],
                marker="^",
                linestyle=":",
                label="XP Δ@10",
                color="#2ca02c",
                alpha=0.8,
            )
            ax_rg.plot(
                x,
                data["xp_diff15"],
                marker="^",
                linestyle="--",
                label="XP Δ@15",
                color="#2ca02c",
                alpha=0.55,
            )
        if data["gold_diff10"]:
            ax_rg.plot(
                x,
                data["gold_diff10"],
                marker="v",
                linestyle=":",
                label="Gold Δ@10",
                color="#9467bd",
                alpha=0.8,
            )
            ax_rg.plot(
                x,
                data["gold_diff15"],
                marker="v",
                linestyle="--",
                label="Gold Δ@15",
                color="#9467bd",
                alpha=0.55,
            )
        ax_rg.axhline(0, color="black", linewidth=1)
        ax_rg.set_xlabel("Match Index (chronological)")
        ax_rg.set_ylabel("XP / Gold Difference")
        ax_rg.set_title(
            f"{player_label} Lane Phase XP & Gold Diffs (Positive = Ahead)"
        )

        # Add legend and grid
        ax_rg.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.20),
            ncol=2,
        )
        ax_rg.grid(alpha=0.3)

        # Prepare stats text
        mxp10 = np.mean(data["xp_diff10"]) if data["xp_diff10"] else 0
        mgold10 = np.mean(data["gold_diff10"]) if data["gold_diff10"] else 0
        parts = [
            f"Games: {len(x)}",
            f"Skipped: {data['opponent_missing']}",
        ]
        if data["xp_diff10"]:
            parts.append(f"Mean XP Δ@10: {mxp10:.0f}")
        if data["gold_diff10"]:
            parts.append(f"Mean Gold Δ@10: {mgold10:.0f}")
        rg_text = "\n".join(parts)

        # Move stats box outside plotting area (top-left margin)
        fig_rg.subplots_adjust(top=0.80)  # ensure room
        fig_rg.text(
            0.01,
            0.985,
            rg_text,
            va="top",
            ha="left",
            fontsize=10,
            bbox=dict(
                boxstyle="round", facecolor="white", alpha=0.85, edgecolor="#999"
            ),
        )

        # Save figure
        save_figure(
            fig_rg,
            f"lane_resource_diffs_{sanitize_player(player_label)}",
            description="lane xp gold diffs",
        )
        plt.close(fig_rg)


def main() -> None:  # pragma: no cover - CLI wrapper
    parser = argparse.ArgumentParser(
        description="Lane phase CS / XP / Gold diff timeline"
    )
    parser.add_argument("IGN", help="In-game name")
    parser.add_argument("TAG", help="Riot tag line")
    parser.add_argument("--matches-dir", default="matches")
    parser.add_argument(
        "-a",
        "--include-aram",
        action="store_true",
        help="Include ARAM matches",
    )
    parser.add_argument(
        "-q", "--queue", nargs="*", type=int, help="Queue ID whitelist"
    )
    parser.add_argument(
        "-M", "--modes", nargs="*", help="Whitelist gameMode values"
    )
    parser.add_argument("--puuid", help="Explicit PUUID (skip lookup)")
    args = parser.parse_args()

    player_label = f"{args.IGN}#{args.TAG}"
    if args.puuid:
        puuid = args.puuid
    else:  # lazy import to avoid circular at module import
        from stats_visualization import league as _league
        import os

        token = os.getenv("RIOT_API_TOKEN")
        if not token:
            raise SystemExit("RIOT_API_TOKEN environment variable is not set")
        puuid = _league.fetch_puuid_by_riot_id(args.IGN, args.TAG, token)

    data = extract_lane_cs_diff_data(
        puuid,
        matches_dir=args.matches_dir,
        include_aram=args.include_aram,
        queue_filter=args.queue,
        game_mode_whitelist=args.modes,
    )
    plot_lane_cs_diff(player_label, data)


if __name__ == "__main__":  # pragma: no cover
    main()
