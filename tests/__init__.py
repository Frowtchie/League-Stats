"""Test package initialization.

Adds a lightweight filter to suppress verbose runtime debug prints emitted by
the visualization modules (lines beginning with the exact prefix ``"[DEBUG]"``)
while leaving all other output (including test diagnostic prints and expected
user‑facing messages) untouched.

This keeps test output concise without modifying production code. If needed
set the environment variable ``LEAGUE_STATS_SHOW_DEBUG=1`` to re-enable the
debug prints during a specific test run.
"""

from __future__ import annotations

import os
import builtins
from typing import Any


_ORIGINAL_PRINT = builtins.print


def _filtered_print(*args: Any, **kwargs: Any) -> None:  # noqa: D401
    """Proxy for :func:`print` that drops lines starting with ``[DEBUG]``.

    Respects the opt-out environment variable to aid local debugging.
    """
    if os.environ.get("LEAGUE_STATS_SHOW_DEBUG"):
        return _ORIGINAL_PRINT(*args, **kwargs)
    if args and isinstance(args[0], str) and args[0].startswith("[DEBUG]"):
        return  # swallow debug line
    return _ORIGINAL_PRINT(*args, **kwargs)


# Install filtered print early so it's active for subsequently imported tests
builtins.print = _filtered_print
