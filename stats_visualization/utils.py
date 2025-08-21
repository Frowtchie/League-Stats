"""Utility helpers for visualization modules and shared logging."""

from __future__ import annotations

from pathlib import Path
import logging
import os
from typing import Optional
from matplotlib.figure import Figure
from typing import Iterable, Sequence, Any


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
    allowed_queue_ids: Optional[Iterable[int]] = None,
    allowed_game_modes: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Return filtered list of match dicts.

    Args:
        matches: Raw loaded match objects.
        include_aram: If False, drop ARAM (gameMode == 'ARAM').
        allowed_queue_ids: If provided, keep only matches whose info.queueId is in set.
        allowed_game_modes: Additional whitelist of gameMode values
            (case-sensitive as provided by API).

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
            print(f"[DEBUG][filter_matches] Skipping match: missing 'info' field: {m}")
            continue
        game_mode = info.get("gameMode")
        if not include_aram and game_mode == "ARAM":
            print(f"[DEBUG][filter_matches] Skipping match: ARAM excluded: {info}")
            continue
        if q_set is not None and info.get("queueId") not in q_set:
            print(
                f"[DEBUG][filter_matches] Skipping match: queueId {info.get('queueId')} "
                f"not in allowed set {q_set}: {info}"
            )
            continue
        if gm_set is not None and game_mode not in gm_set:
            print(
                f"[DEBUG][filter_matches] Skipping match: gameMode {game_mode} "
                f"not in allowed set {gm_set}: {info}"
            )
            continue
        print(f"[DEBUG][filter_matches] Keeping match: {info}")
        out.append(m)
    print(f"[DEBUG][filter_matches] Returning {len(out)} matches out of {len(matches)}")
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


def setup_file_logging(
    log_path: str = "logs/league_stats.log", *, level: int = logging.INFO
) -> None:
    """Attach a FileHandler to the root logger for persistent logs.

    Safe to call multiple times; avoids duplicate handlers for the same file.
    """
    Path(os.path.dirname(log_path) or ".").mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    # Ensure root logger permits messages at desired level (e.g., INFO).
    # Streamlit often leaves the root at WARNING; drop it to `level`
    # if the current level is higher than the desired level.
    try:
        current_level = root.level
        if current_level == logging.NOTSET or current_level > level:
            root.setLevel(level)
    except Exception:
        # Best-effort; proceed even if we cannot adjust the level.
        pass
    norm_target = os.path.abspath(log_path)
    for h in root.handlers:
        if isinstance(h, logging.FileHandler):
            try:
                if os.path.abspath(getattr(h, "baseFilename", "")) == norm_target:
                    return
            except Exception:
                continue
    fh = logging.FileHandler(norm_target, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root.addHandler(fh)
