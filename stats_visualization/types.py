"""Minimal shim to avoid shadowing the stdlib :mod:`types` module.

TypedDict definitions live in ``stats_visualization.viz_types``.
This file re-exports the real stdlib ``types`` symbols so that importing
``typing`` works even if this directory is first on ``sys.path``.
"""

from importlib import import_module as _im

_stdlib_types = _im("types")  # stdlib module
for _n in dir(_stdlib_types):
    if not _n.startswith("__"):
        globals()[_n] = getattr(_stdlib_types, _n)

__all__ = [n for n in globals() if not n.startswith("__")]

del _im, _stdlib_types, _n
