"""Utility helpers for visualization modules."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from matplotlib.figure import Figure  # type: ignore


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
