"""Streamlit GUI for League-Stats.

Preferred run commands (from project root):
    streamlit run stats_visualization/gui_app.py
Or module form:
    python -m streamlit run stats_visualization/gui_app.py

Note: Running `python -m stats_visualization.gui_app` or `python stats_visualization/gui_app.py`
WON'T start the UI because Streamlit must launch the script. Those modes are only for
linting / import validation. If you run this file directly and see no UI, re-run with streamlit.

This module keeps business logic in existing core modules (league, analyze) and only adds UI glue.
"""

from __future__ import annotations

import os
import sys
import time
import base64
from pathlib import Path
import logging
from typing import Iterable, Optional, List

import streamlit as st

# Add project root to Python path for Streamlit Cloud compatibility
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Support both execution from project root (absolute import) and from inside the package directory
try:  # pragma: no cover - import robustness
    from . import analyze, league
except (ImportError, ValueError):  # ValueError for relative import in non-package
    try:
        from stats_visualization import analyze, league
    except ImportError:
        # Direct import as fallback for Streamlit Cloud
        import analyze
        import league

# Shared logging: write GUI actions into logs/league_stats.log
try:  # pragma: no cover - safe in Streamlit reloads
    from stats_visualization.utils import setup_file_logging
    setup_file_logging()
except ImportError:
    try:
        from utils import setup_file_logging
        setup_file_logging()
    except ImportError:
        # Fallback: basic logging setup
        logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")

# Mapping of user-friendly labels to Queue IDs
QUEUE_ID_MAP = {
    "Solo/Duo": [420],
    "Flex": [440],
    "Normal": [400, 430],
    "ARAM": [450],
    "URF": [900],
}


def _list_pngs() -> list[Path]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return sorted(p for p in OUTPUT_DIR.glob("*.png"))


def _generate_all(
    ign: str,
    tag: str,
    token: str,
    *,
    queue_filter: Optional[Iterable[int]],
    game_mode_whitelist: Optional[Iterable[str]],
    clean: bool,
    min_matches: int,
    fetch_count: int,
) -> tuple[str, Optional[str]]:
    """Fetch (if needed) and generate all visuals. Returns (status, error)."""
    try:
        logger.info("GUI: Resolving PUUID for %s#%s", ign, tag)
        puuid, real_name, real_tag = league.fetch_puuid_and_name_by_riot_id(ign, tag, token)
    except Exception as e:  # pragma: no cover (network)
        logger.error("GUI: Failed to resolve PUUID for %s#%s: %s", ign, tag, e)
        return "Failed to resolve PUUID", str(e)

    try:
        logger.info(
            "GUI: Ensuring matches for %s#%s (min=%d, fetch_count=%d)",
            real_name,
            real_tag,
            min_matches,
            fetch_count,
        )
        league.ensure_matches_for_player(
            puuid,
            token,
            matches_dir="matches",
            min_matches=min_matches,
            fetch_count=fetch_count,
        )
    except Exception as e:  # pragma: no cover
        logger.error("GUI: Failed during match fetch for %s#%s: %s", real_name, real_tag, e)
        return "Failed during match fetch", str(e)

    try:
        logger.info("GUI: Generating all visuals for %s#%s", real_name, real_tag)
        analyze.generate_all_visuals(
            f"{real_name}#{real_tag}",
            puuid,
            queue_filter=list(queue_filter) if queue_filter is not None else None,
            game_mode_whitelist=(
                list(game_mode_whitelist) if game_mode_whitelist is not None else None
            ),
            clean=clean,
            matches_dir="matches",
        )
    except Exception as e:  # pragma: no cover
        logger.error("GUI: Visualization generation failed for %s#%s: %s", real_name, real_tag, e)
        return "Visualization generation failed", str(e)
    logger.info("GUI: Success generating visuals for %s#%s", real_name, real_tag)
    return "Success", None


def _count_player_matches(puuid: str) -> int:
    from json import load

    count = 0
    for fp in Path("matches").glob("*.json"):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = load(f)
            if any(p.get("puuid") == puuid for p in data.get("info", {}).get("participants", [])):
                count += 1
        except Exception:  # pragma: no cover
            continue
    return count


def main():  # noqa: C901 (complexity acceptable for UI glue)
    st.set_page_config(page_title="League-Stats GUI", layout="wide")
    st.title("League-Stats GUI (Prototype)")
    st.caption(
        "Prototype graphical interface layering on existing CLI logic. "
        "Uses bulk chart generation; expect a short wait on each run."
    )

    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        st.error(
            "RIOT_API_TOKEN environment variable not set. Edit config.env and restart "
            "(scripts auto-load it)."
        )
        st.stop()

    with st.sidebar:
        st.header("Player")
        ign = st.text_input("IGN", value="Frowtch")
        tag = st.text_input("Tag Line", value="blue")
        # Dropdown menu for queue selection
        queue_label = st.selectbox(
            "Select Game Mode",
            options=list(QUEUE_ID_MAP.keys()),
            help="Choose a game mode to filter matches.",
        )
        st.header("Generation")
        clean = st.checkbox("Clean output/ before build", value=True)
        min_matches = st.number_input("Min local matches", 1, 100, 5)
        fetch_count = st.number_input("Fetch count when needed", 1, 100, 10)
        run_btn = st.button("Generate / Refresh Charts", type="primary")
        st.markdown("---")
        st.caption(
            "Tip: Generation reuses existing logic in analyze.generate_all_visuals. "
            "Future versions may support per-chart incremental updates."
        )

    # Derived filters
    queue_filter: Optional[List[int]] = None
    # Get the corresponding Queue IDs from the selected label
    queue_filter = QUEUE_ID_MAP.get(queue_label, None)
    mode_whitelist = None

    # Auto show current match count if player resolvable
    puuid = None
    if ign and tag:
        try:
            puuid = league.fetch_puuid_by_riot_id(ign, tag, token)
        except Exception:  # pragma: no cover (network variability)
            puuid = None
    if puuid:
        with st.expander("Local Data Summary", expanded=False):
            st.write(f"Local stored matches involving player: {_count_player_matches(puuid)}")

    if run_btn:
        start = time.time()
        logger.info("GUI: Run requested from sidebar")
        with st.status("Generating charts", expanded=True) as status:
            status.write("Resolving player, ensuring matches, building visualizations...")
            state, error = _generate_all(
                ign,
                tag,
                token,
                queue_filter=queue_filter,
                game_mode_whitelist=mode_whitelist,
                clean=clean,
                min_matches=int(min_matches),
                fetch_count=int(fetch_count),
            )
            if state == "Success":
                logger.info("GUI: Generation complete in %.2fs", time.time() - start)
                status.update(label="Generation complete", state="complete", expanded=False)
            else:
                logger.warning("GUI: Generation error (%s): %s", state, error or state)
                status.update(label=state, state="error", expanded=True)
                st.error(error or state)
        st.toast(f"Completed in {time.time() - start:.1f}s", icon="✅")

    st.subheader("Generated Charts")

    # Styling (thumbnails + modal overlay)
    st.markdown(
        """
        <style>
    .league-thumb img {transition:transform .15s ease,
        box-shadow .15s ease; border:1px solid #444;
        border-radius:4px;}
    .league-thumb img:hover {transform:scale(1.02);
        box-shadow:0 2px 10px rgba(0,0,0,0.45);}
    .league-modal-overlay {position:fixed; top:0; left:0; right:0; bottom:0;
        background:rgba(0,0,0,0.83);
        z-index:9999; display:flex; flex-direction:column; align-items:center;
        justify-content:center; padding:1.5rem;}
    .league-modal-inner {max-width:94%; max-height:90%; text-align:center;}
    .league-modal-inner img {max-width:100%; max-height:80vh;
        border:2px solid #555; border-radius:8px;
        box-shadow:0 4px 24px rgba(0,0,0,0.65);}
    .league-modal-bar {display:flex; align-items:center;
        justify-content:space-between; width:100%; margin-bottom:8px; gap:8px;}
    .league-modal-title {flex:1; color:#ddd; font-size:0.75rem; text-align:left;
        word-break:break-all;}
    .league-modal-close {color:#fff !important; text-decoration:none; font-size:1.4rem;
        line-height:1; padding:2px 10px; border:1px solid #666; border-radius:6px;
        background:rgba(0,0,0,0.45); display:inline-block;}
    .league-modal-close:hover {background:rgba(255,255,255,0.15);}
    .league-modal-actions {margin-top:10px; display:flex; align-items:center;
        justify-content:center; gap:12px;}
    .league-modal-close-text {font-size:0.7rem; color:#bbb; text-decoration:none;}
    .league-modal-close-text:hover {color:#fff; text-decoration:underline;}
    .league-dl-btn {margin-top:10px; display:inline-block; background:#1e3a8a; color:#fff;
        padding:6px 12px; border-radius:4px; text-decoration:none; font-size:0.85rem;
        border:1px solid #294797;}
    .league-dl-btn:hover {background:#2649a6;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Handle query param close (avoids 403 from raw POST forms)
    params = st.query_params  # modern API (experimental_get_query_params deprecated)
    if "close" in params:
        if "modal_image" in st.session_state:
            st.session_state.modal_image = None
        # Clear all query params (removes ?close=1)
        try:
            st.query_params.clear()
        except Exception:  # pragma: no cover
            pass
        st.rerun()

    # Session-based modal (URL kept clean except temporary ?close)
    if "modal_image" not in st.session_state:
        st.session_state.modal_image = None

    if st.session_state.modal_image:
        selected_img = st.session_state.modal_image
        large_path = OUTPUT_DIR / str(selected_img)
        if large_path.exists():
            try:
                b64_large = base64.b64encode(large_path.read_bytes()).decode("utf-8")
            except Exception:
                b64_large = ""
            st.markdown(
                f"""
                <div class='league-modal-overlay'>
                    <div class='league-modal-inner'>
                        <div class='league-modal-bar'>
                            <div class='league-modal-title'>{selected_img}</div>
                                     <a href='?close=1' target='_self'
                                         class='league-modal-close'
                                         aria-label='Close'
                                         title='Close'>&times;</a>
                        </div>
                        <img src='data:image/png;base64,{b64_large}' alt='{selected_img}' />
                        <div class='league-modal-actions'>
                                     <a class='league-dl-btn'
                                         href='data:image/png;base64,{b64_large}'
                                         download='{selected_img}'>Download</a>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # (Legacy POST close removed; using query param now)

    images = _list_pngs()
    if not images:
        st.info("No charts yet. Click 'Generate / Refresh Charts' in the sidebar.")
    else:
        cols_per_row = 3
        for i in range(0, len(images), cols_per_row):
            row = images[i : (i + cols_per_row)]
            cols = st.columns(len(row))
            for col, img_path in zip(cols, row):
                try:
                    b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
                except Exception:
                    col.warning("Failed to load image")
                    continue
                with col:
                    if st.button(
                        label=f"🔍 {img_path.name}",
                        key=f"open_{img_path.name}",
                        help="Open full size",
                    ):
                        st.session_state.modal_image = img_path.name
                        st.rerun()
                    thumb_html = (
                        "<div class='league-thumb'>"
                        f"<img src='data:image/png;base64,{b64}' alt='{img_path.name}' "
                        "style='width:100%;cursor:pointer;pointer-events:none;'/>"
                        "</div>"
                        f"<div style='text-align:center;font-size:0.7rem;margin-top:4px;'>"
                        f"{img_path.name}</div>"
                    )
                    st.markdown(thumb_html, unsafe_allow_html=True)

    with st.expander("Advanced / Debug"):
        st.code(
            "python -m stats_visualization.league {ign} {tag} 10\n"
            "python analyze.py -i {ign} {tag} -g --ranked-only",
            language="bash",
        )
        st.caption("Equivalent CLI commands for reference.")


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    main()
