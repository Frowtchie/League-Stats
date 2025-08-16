"""Utility helpers for visualization modules."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from matplotlib.figure import Figure  # type: ignore
from typing import Iterable, Sequence, Any, Dict, List
import os


def clean_output(output_dir: str | Path = "output") -> int:
    """Remove existing PNG files in the output directory.

    Returns number of files removed. Silently returns 0 if directory missing.
    """
    p = Path(output_dir)
    if not p.exists():
        return 0
    count = 0
    for f in p.glob("*.png"):
        try:
            f.unlink()
            count += 1
        except OSError:
            pass
    if count:
        print(f"Cleaned output directory: removed {count} file(s)")
    else:
        print("Output directory already clean")
    return count


def filter_matches(
    matches: Sequence[dict[str, Any]],
    *,
    include_aram: bool = False,
    allowed_queue_ids: Iterable[int] | None = None,
    allowed_game_modes: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Return filtered list of match dicts.

    Args:
        matches: Raw loaded match objects.
        include_aram: If False, drop ARAM (gameMode == 'ARAM').
        allowed_queue_ids: If provided, keep only matches whose info.queueId is in set.
        allowed_game_modes: Additional whitelist of gameMode values (case-sensitive as provided by API).

    Notes:
        - Silently skips matches missing 'info'.
        - If both allowed_queue_ids and allowed_game_modes are given, a match must satisfy both.
    """
    out: list[dict[str, Any]] = []
    q_set = set(allowed_queue_ids) if allowed_queue_ids else None
    gm_set = set(allowed_game_modes) if allowed_game_modes else None
    for m in matches:
        info = m.get("info") or {}
        if not info:
            continue
        game_mode = info.get("gameMode")
        if not include_aram and game_mode == "ARAM":
            continue
        if q_set is not None and info.get("queueId") not in q_set:
            continue
        if gm_set is not None and game_mode not in gm_set:
            continue
        out.append(m)
    return out


def save_figure(
    fig: Figure,
    filename: str,
    output_dir: str | Path = "output",
    description: Optional[str] = None,
    dpi: int = 300,
) -> Path:
    """Save a matplotlib figure to the output directory.

    Args:
        fig: Matplotlib Figure instance.
        filename: Target filename (with or without .png). Can already include player identifier.
        output_dir: Directory to save into (created if missing).
        description: Optional human‑readable label for log message.
        dpi: Image DPI.
    Returns:
        Path to saved file.
    """
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(exist_ok=True)
    if not filename.lower().endswith(".png"):
        filename += ".png"
    path = out_dir_path / filename
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    if description:
        print(f"Saved {description} to {path}")
    else:
        print(f"Saved figure to {path}")
    return path


def sanitize_player(name: str) -> str:
    """Sanitize a Riot player display name for filesystem use."""
    return name.replace("#", "_")
