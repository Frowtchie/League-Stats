# Visualizations Catalog

| File | Output Name Pattern | Focus | Key Insights |
|------|---------------------|-------|-------------|
| graph_drakes.py | drake_analysis_<player>.png | Dragon counts & trends | Player vs enemy drakes, temporal control (ARAM excluded by default; filtering flags) |
| graph_barons_heralds.py | barons_heralds_<player>.png | Baron/Herald control | Objective advantage & win correlation (ARAM excluded by default; filtering flags) |
| graph_first_bloods.py | first_bloods_<player>.png | Early aggression & outcomes | Early performance vs win rate |
| graph_kills.py | kills_analysis_<player>.png | Kills/KDA progression | Trend lines & participation (filtering flags) |
| farming_analysis.py (farming) | farming_performance_<player>.png | CS distribution & role variance | Consistency & role differences (filtering flags) |
| farming_analysis.py (gold) | gold_efficiency_<player>.png | Gold & damage efficiency | Correlation & economy pacing (filtering flags) |
| farming_analysis.py (roles) | role_economy_<player>.png | Economy by role | Comparative benchmarks (filtering flags) |
| jungle_clear_analysis.py | jungle_clear_analysis.png | First clear & efficiency | Clear timing consistency (filtering flags) |
| objective_analysis.py (control) | objective_control_<player>.png | Team objective averages | Control vs win indicators (ARAM excluded by default; filtering flags) |
| objective_analysis.py (first) | first_objectives_<player>.png | First objective success | Early control impact (ARAM excluded by default; filtering flags) |
| personal_performance.py (trends) | performance_trends_<player>.png | KDA & win rate trends | Improvement trajectory (filtering flags) |
| personal_performance.py (champions) | champion_performance_<player>.png | Champion stats | Champion pool strengths (filtering flags) |
| personal_performance.py (roles) | role_performance_<player>.png | Role performance | Role-specific consistency (filtering flags) |

## Naming Conventions
- Replace `#` with `_` in player identifier.
- Lowercase topic segments.

## Adding a New Visualization
1. Create script in `visualizations/`.
2. Add save call with pattern `<topic>_<player>.png`.
3. Update this catalog and `cli_reference.md`.
4. Ensure outputs go to `output/`.

## Figure Saving & Utilities
All visualization scripts now use the centralized helper `save_figure` from `stats_visualization/utils.py`.

Most scripts now support centralized match filtering via shared flags:
`--include-aram`, `--queue`, `--ranked-only`, `--modes`. These combine (logical AND) and default to excluding ARAM with no queue/mode restriction.

Benefits:
- Consistent DPI (300) and tight bounding box.
- Single place to adjust global saving behavior (naming, formats later, etc.).
- Automatic creation of the `output/` directory.

Usage pattern:
```
from stats_visualization.utils import save_figure, sanitize_player

fig, ax = plt.subplots(...)
... # plotting logic
save_figure(fig, f"my_chart_{sanitize_player(player_name)}", description="my chart")
```

When adding new visualizations, prefer this utility instead of calling `plt.savefig` directly. If a different image format or additional metadata is needed in the future, extend `save_figure` once and all scripts benefit automatically.
