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
import time
import base64
from pathlib import Path
from typing import Iterable, Optional, List

import streamlit as st

# Support both execution from project root (absolute import) and from inside the package directory
try:  # pragma: no cover - import robustness
    from . import analyze, league
except Exception:  # noqa: BLE001 - broad fallback acceptable here
    from stats_visualization import analyze, league

OUTPUT_DIR = Path("output")


def _list_pngs() -> list[Path]:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return sorted(p for p in OUTPUT_DIR.glob("*.png"))


def _generate_all(
    ign: str,
    tag: str,
    token: str,
    *,
    include_aram: bool,
    queue_filter: Optional[Iterable[int]],
    game_mode_whitelist: Optional[Iterable[str]],
    clean: bool,
    min_matches: int,
    fetch_count: int,
) -> tuple[str, Optional[str]]:
    """Fetch (if needed) and generate all visuals. Returns (status, error)."""
    try:
        puuid = league.fetch_puuid_by_riot_id(ign, tag, token)
    except Exception as e:  # pragma: no cover (network)
        return "Failed to resolve PUUID", str(e)

    try:
        league.ensure_matches_for_player(
            puuid,
            token,
            matches_dir="matches",
            min_matches=min_matches,
            fetch_count=fetch_count,
        )
    except Exception as e:  # pragma: no cover
        return "Failed during match fetch", str(e)

    try:
        analyze.generate_all_visuals(
            f"{ign}#{tag}",
            puuid,
            include_aram=include_aram,
            queue_filter=list(queue_filter) if queue_filter is not None else None,
            game_mode_whitelist=(
                list(game_mode_whitelist) if game_mode_whitelist is not None else None
            ),
            clean=clean,
            matches_dir="matches",
        )
    except Exception as e:  # pragma: no cover
        return "Visualization generation failed", str(e)
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
            "RIOT_API_TOKEN environment variable not set. Edit config.env and restart (scripts auto-load it)."
        )
        st.stop()

    with st.sidebar:
        st.header("Player")
        ign = st.text_input("IGN", value="Frowtch")
        tag = st.text_input("Tag Line", value="blue")
        st.header("Filters")
        ranked_only = st.checkbox("Ranked Only (Solo/Flex)", value=True, help="Queues 420 & 440")
        include_aram = st.checkbox("Include ARAM", value=False)
        queue_ids_raw = st.text_input(
            "Queue IDs (space separated)",
            value="" if ranked_only else "",
            help=(
                "Overrides 'Ranked Only' when provided. Common queues: "
                "420=Ranked Solo, 440=Ranked Flex, 400=Draft Pick, 430=Blind Pick, "
                "450=ARAM, 490=Quickplay, 700=Clash, 900=URF, 920=Poro King, 1020=One For All, "
                "830/840/850=Intro/Beginner/Intermediate Bots."
            ),
        )
        modes_raw = st.text_input(
            "Game Modes (space separated)", value="", help="e.g. CLASSIC CHERRY"
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
    if ranked_only:
        queue_filter = [420, 440]
    if queue_ids_raw.strip():  # explicit queue IDs override ranked shortcut
        try:
            queue_filter = [int(q) for q in queue_ids_raw.split()] if queue_ids_raw else None
        except ValueError:
            st.warning("Invalid queue IDs ignored (must be integers).")
    mode_whitelist = modes_raw.split() if modes_raw.strip() else None

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
        with st.status("Generating charts", expanded=True) as status:
            status.write("Resolving player, ensuring matches, building visualizations...")
            state, error = _generate_all(
                ign,
                tag,
                token,
                include_aram=include_aram,
                queue_filter=queue_filter,
                game_mode_whitelist=mode_whitelist,
                clean=clean,
                min_matches=int(min_matches),
                fetch_count=int(fetch_count),
            )
            if state == "Success":
                status.update(label="Generation complete", state="complete", expanded=False)
            else:
                status.update(label=state, state="error", expanded=True)
                st.error(error or state)
        st.toast(f"Completed in {time.time() - start:.1f}s", icon="✅")

    st.subheader("Generated Charts")

    # Styling (thumbnails + modal overlay)
    st.markdown(
        """
        <style>
    .league-thumb img {transition:transform .15s ease, box-shadow .15s ease; border:1px solid #444; border-radius:4px;}
    .league-thumb img:hover {transform:scale(1.02); box-shadow:0 2px 10px rgba(0,0,0,0.45);}
    .league-modal-overlay {position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.83); z-index:9999;
        display:flex; flex-direction:column; align-items:center; justify-content:center; padding:1.5rem;}
    .league-modal-inner {max-width:94%; max-height:90%; text-align:center;}
    .league-modal-inner img {max-width:100%; max-height:80vh; border:2px solid #555; border-radius:8px;
        box-shadow:0 4px 24px rgba(0,0,0,0.65);}
    .league-modal-bar {display:flex; align-items:center; justify-content:space-between; width:100%;
        margin-bottom:8px; gap:8px;}
    .league-modal-title {flex:1; color:#ddd; font-size:0.75rem; text-align:left; word-break:break-all;}
    .league-modal-close {color:#fff !important; text-decoration:none; font-size:1.4rem; line-height:1; padding:2px 10px;
        border:1px solid #666; border-radius:6px; background:rgba(0,0,0,0.45); display:inline-block;}
    .league-modal-close:hover {background:rgba(255,255,255,0.15);}
    .league-modal-actions {margin-top:10px; display:flex; align-items:center; justify-content:center;
        gap:12px;}
    .league-modal-close-text {font-size:0.7rem; color:#bbb; text-decoration:none;}
    .league-modal-close-text:hover {color:#fff; text-decoration:underline;}
    .league-dl-btn {margin-top:10px; display:inline-block; background:#1e3a8a; color:#fff; padding:6px 12px;
        border-radius:4px; text-decoration:none; font-size:0.85rem; border:1px solid #294797;}
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
            row = images[i : i + cols_per_row]
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
                        f"<div style='text-align:center;font-size:0.7rem;margin-top:4px;'>{img_path.name}</div>"
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
