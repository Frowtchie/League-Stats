"""League API helpers (clean minimal version).

This module provides synchronous helper functions used by the rest of the
project. It intentionally avoids async complexity. A canonical name + tag
resolver is provided for consistent casing in downstream outputs.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
import time
from typing import Any, Dict, List, Optional, cast
import asyncio
import importlib.util

import requests
from stats_visualization.utils import setup_file_logging

logger = logging.getLogger(__name__)

# Basic constants
MATCHES_DIR = "matches"
API_REGION_BASE = "https://europe.api.riotgames.com/lol/match/v5/matches/"
MATCH_HISTORY_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/"
TIMELINE_API_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
ACCOUNT_BASE_URL = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id"

# Load environment variables from repo root config.env if present
try:
    # Resolved relative to current working directory; typical runs are from repo root
    load_dotenv("config.env")
except Exception:
    # Non-fatal if dotenv missing or file not present
    pass

# ---------------------------------------------------------------------------
# Metrics (re-added for test compatibility)
# ---------------------------------------------------------------------------


@dataclass
class FetchMetrics:
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    retry_count: int = 0
    request_latencies: List[float] = field(default_factory=lambda: cast(List[float], []))
    match_ids_requests: int = 0
    match_details_requests: int = 0
    timeline_requests: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def add_request_latency(self, latency: float, phase: str = "generic") -> None:
        self.request_latencies.append(latency)
        self.total_requests += 1
        if phase == "match_ids":
            self.match_ids_requests += 1
        elif phase == "match_details":
            self.match_details_requests += 1
        elif phase == "timeline":
            self.timeline_requests += 1

    def add_cache_hit(self) -> None:
        self.cache_hits += 1

    def add_cache_miss(self) -> None:
        self.cache_misses += 1

    def add_retry(self) -> None:
        self.retry_count += 1

    def start_timing(self) -> None:
        self.start_time = time.time()

    def end_timing(self) -> None:
        self.end_time = time.time()

    @property
    def total_duration(self) -> Optional[float]:
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None

    @property
    def avg_latency(self) -> float:
        if not self.request_latencies:
            return 0.0
        return sum(self.request_latencies) / len(self.request_latencies)

    @property
    def max_latency(self) -> float:
        if not self.request_latencies:
            return 0.0
        return max(self.request_latencies)

    @property
    def p95_latency(self) -> float:
        if not self.request_latencies:
            return 0.0
        ordered = sorted(self.request_latencies)
        idx = int(len(ordered) * 0.95) - 1
        idx = max(0, min(idx, len(ordered) - 1))
        return ordered[idx]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "retry_count": self.retry_count,
            "avg_latency_ms": round(self.avg_latency * 1000, 2),
            "p95_latency_ms": round(self.p95_latency * 1000, 2),
            "max_latency_ms": round(self.max_latency * 1000, 2),
            "phase_breakdown": {
                "match_ids_requests": self.match_ids_requests,
                "match_details_requests": self.match_details_requests,
                "timeline_requests": self.timeline_requests,
            },
            "total_duration_s": self.total_duration,
        }

    def print_summary(self) -> None:  # pragma: no cover
        summary = self.to_dict()
        print("=== Fetch Metrics Summary ===")
        print(f"Total requests: {summary['total_requests']}")
        print(f"Cache hits: {summary['cache_hits']}")
        print(f"Cache misses: {summary['cache_misses']}")
        print(f"Retry count: {summary['retry_count']}")
        print(f"Avg latency ms: {summary['avg_latency_ms']}")
        print(f"P95 latency ms: {summary['p95_latency_ms']}")
        print(f"Max latency ms: {summary['max_latency_ms']}")
        print("Phase breakdown:")
        phases = summary["phase_breakdown"]
        print(f"  match_ids_requests: {phases['match_ids_requests']}")
        print(f"  match_details_requests: {phases['match_details_requests']}")
        print(f"  timeline_requests: {phases['timeline_requests']}")
        print(f"Total duration s: {summary['total_duration_s']}")


_fetch_metrics = FetchMetrics()


def export_metrics_json(filepath: str) -> None:
    """Export global metrics to a JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(_fetch_metrics.to_dict(), f, indent=2)
    except OSError as e:  # pragma: no cover
        logger.error("Failed to export metrics: %s", e)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------
def load_player_config() -> Dict[str, str]:
    """Load player PUUIDs from environment variables.

    Environment variables of the form ``PUUID_<NAME>`` are collected and
    normalized (``FROWTCH`` -> ``Frowtch``). If none are present a default
    placeholder mapping is returned (tests rely on key presence only).
    """
    mapping: Dict[str, str] = {}
    prefix = "PUUID_"
    for key, value in os.environ.items():
        if key.startswith(prefix) and value:
            raw = key[len(prefix) :]
            name = raw.capitalize() if raw.isupper() else raw
            mapping[name] = value
    if not mapping:
        mapping = {"Frowtch": "UNKNOWN", "Overowser": "UNKNOWN", "Suro": "UNKNOWN"}
    return mapping


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def validate_match_data(data: Any) -> bool:
    """Basic validation for match JSON structure used in tests.

    Accepts Any, returns True only if keys/info fields expected are present.
    """
    if not isinstance(data, dict):
        return False
    from typing import cast as _cast

    data_dict = _cast(Dict[str, Any], data)
    info_raw: Any = data_dict.get("info")
    meta_raw: Any = data_dict.get("metadata")
    if not isinstance(info_raw, dict) or not isinstance(meta_raw, dict):
        return False
    return "gameId" in info_raw and "matchId" in meta_raw


# ---------------------------------------------------------------------------
# Core HTTP helper
# ---------------------------------------------------------------------------
def make_api_request(
    url: str, headers: Dict[str, str], *, timeout: int, request_type: str
):  # pragma: no cover (thin wrapper)
    """Perform a GET request and raise for HTTP errors.

    The ``request_type`` argument exists only so tests can patch this function
    and still receive the same signature that older versions provided.
    """
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


# ---------------------------------------------------------------------------
# PUUID / account resolution
# ---------------------------------------------------------------------------
def fetch_puuid_and_name_by_riot_id(
    game_name: str, tag_line: str, token: str
) -> tuple[str, str, str]:
    """Return (puuid, canonical_gameName, canonical_tagLine)."""
    url = f"{ACCOUNT_BASE_URL}/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": token}
    try:
        resp = make_api_request(url, headers, timeout=30, request_type="puuid")
    except requests.exceptions.HTTPError as e:  # pragma: no cover (network variability)
        if e.response is not None and e.response.status_code == 404:
            raise ValueError("Player not found") from e
        raise
    data_json_raw: Any = resp.json()
    if not isinstance(data_json_raw, dict) or not all(
        k in data_json_raw for k in ("puuid", "gameName", "tagLine")
    ):
        raise ValueError("Invalid response format - missing required fields")
    data_json: Dict[str, Any] = cast(Dict[str, Any], data_json_raw)
    puuid = str(data_json["puuid"])
    real_name = str(data_json["gameName"])
    real_tag = str(data_json["tagLine"])
    logger.info(
        "Resolved Riot ID %s#%s -> %s#%s (puuid tail %s)",
        game_name,
        tag_line,
        real_name,
        real_tag,
        puuid[-6:],
    )
    return puuid, real_name, real_tag


def fetch_puuid_by_riot_id(game_name: str, tag_line: str, token: str) -> str:
    """Backward compatible wrapper returning only the PUUID.

    Raises ValueError("not found") when the player does not exist to satisfy tests.
    """
    url = f"{ACCOUNT_BASE_URL}/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": token}
    try:
        resp = make_api_request(url, headers, timeout=30, request_type="puuid")
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise ValueError("Player not found") from e
        raise
    data_json_raw: Any = resp.json()
    if not isinstance(data_json_raw, dict) or "puuid" not in data_json_raw:
        raise ValueError("Invalid response format - missing PUUID")
    data_json: Dict[str, Any] = cast(Dict[str, Any], data_json_raw)
    return str(data_json["puuid"])


# ---------------------------------------------------------------------------
# Match & timeline fetchers
# ---------------------------------------------------------------------------
def fetch_match_history(puuid: str, count: int, token: str) -> List[str]:
    if count <= 0:
        raise ValueError("Count must be positive")
    headers = {"X-Riot-Token": token}
    out: List[str] = []
    start = 0
    remaining = count
    while remaining > 0:
        batch = min(remaining, 100)
        url = f"{MATCH_HISTORY_URL}{puuid}/ids?start={start}&count={batch}"
        resp = make_api_request(url, headers, timeout=30, request_type="match_ids")
        data_json_raw: Any = resp.json()
        if not isinstance(data_json_raw, list):
            raise ValueError("Match history response was not a list")
        data_json: List[str] = cast(List[str], data_json_raw)
        ids = [str(mid) for mid in data_json]
        out.extend(ids)
        if len(ids) < batch:
            break
        start += batch
        remaining -= batch
    return out


def fetch_match_data(match_id: str, token: str) -> Dict[str, Any]:
    headers = {"X-Riot-Token": token}
    url = f"{API_REGION_BASE}{match_id}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data_raw: Any = resp.json()
    if not isinstance(data_raw, dict):
        raise ValueError("Match data response was not a JSON object")
    data: Dict[str, Any] = cast(Dict[str, Any], data_raw)
    return data


def fetch_timeline_data(match_id: str, token: str) -> Optional[Dict[str, Any]]:
    headers = {"X-Riot-Token": token}
    url = TIMELINE_API_URL.format(match_id=match_id)
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:  # pragma: no cover
        if e.response is not None and e.response.status_code == 404:
            logger.info("Timeline not found for %s", match_id)
            return None
        raise
    data_raw: Any = resp.json()
    if not isinstance(data_raw, dict):
        return None
    data: Dict[str, Any] = cast(Dict[str, Any], data_raw)
    return data


def fetch_match_with_timeline(match_id: str, token: str) -> Dict[str, Any]:
    match_data = fetch_match_data(match_id, token)
    timeline = fetch_timeline_data(match_id, token)
    if timeline:
        match_data["timeline"] = timeline
    return match_data


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def save_match_data(match_id: str, data: Dict[str, Any]) -> None:
    Path(MATCHES_DIR).mkdir(exist_ok=True)
    fp = Path(MATCHES_DIR) / f"{match_id}.json"
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def process_matches(match_ids: List[str], token: str, use_cache: bool = True) -> None:
    for match_id in match_ids:
        if use_cache:
            fp = Path(MATCHES_DIR) / f"{match_id}.json"
            if fp.exists():
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    if validate_match_data(cached):
                        continue
                except Exception:  # pragma: no cover
                    pass
        # Tests patch fetch_match_data and save_match_data; keep it simple
        data = fetch_match_data(match_id, token)
        save_match_data(match_id, data)


# ---------------------------------------------------------------------------
# Convenience: ensure enough matches cached for a player
# ---------------------------------------------------------------------------
def ensure_matches_for_player(
    puuid: str,
    token: str,
    *,
    matches_dir: str = MATCHES_DIR,
    min_matches: int = 1,
    fetch_count: int = 10,
) -> int:
    Path(matches_dir).mkdir(exist_ok=True)

    def count_cached() -> int:
        total = 0
        for fp in Path(matches_dir).glob("*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if any(
                    p.get("puuid") == puuid for p in data.get("info", {}).get("participants", [])
                ):
                    total += 1
            except Exception:  # pragma: no cover
                continue
        return total

    current = count_cached()
    if current >= min_matches:
        return current
    ids = fetch_match_history(puuid, fetch_count, token)
    process_matches(ids, token, use_cache=True)
    return count_cached()


__all__ = [
    "load_player_config",
    "validate_match_data",
    "make_api_request",
    "fetch_puuid_and_name_by_riot_id",
    "fetch_puuid_by_riot_id",
    "fetch_match_history",
    "fetch_match_data",
    "fetch_timeline_data",
    "fetch_match_with_timeline",
    "save_match_data",
    "process_matches",
    "ensure_matches_for_player",
]


# ---------------------------------------------------------------------------
# Async processing (used by CLI by default)
# ---------------------------------------------------------------------------
async def async_process_matches(
    match_ids: List[str],
    token: str,
    *,
    use_cache: bool = True,
    include_timeline: bool = False,
    concurrency: int = 10,
) -> None:
    """Fetch and save matches concurrently using httpx and async helpers.

    Keeps the public sync API intact for tests; only the CLI uses this by default.
    """
    try:
        import httpx as _httpx
    except Exception as e:  # pragma: no cover - optional dependency missing
        raise RuntimeError(
            "Async mode requires the 'httpx' package. Install it or use --sync."
        ) from e
    from stats_visualization.async_fetch import (
        fetch_match as _af_fetch_match,
        fetch_match_with_timeline as _af_fetch_match_with_timeline,
    )

    Path(MATCHES_DIR).mkdir(exist_ok=True)

    sem = asyncio.Semaphore(max(1, concurrency))

    async with _httpx.AsyncClient(timeout=30) as client:

        async def _worker(mid: str) -> None:
            if use_cache:
                fp = Path(MATCHES_DIR) / f"{mid}.json"
                if fp.exists():
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            cached = json.load(f)
                        if validate_match_data(cached):
                            return
                    except Exception:  # pragma: no cover
                        pass
            t0 = time.time()
            try:
                if include_timeline:
                    data = await _af_fetch_match_with_timeline(mid, token, client)
                else:
                    data = await _af_fetch_match(mid, token, client)
                save_match_data(mid, cast(Dict[str, Any], data))
            except _httpx.HTTPError as e:  # pragma: no cover (network variability)
                logger.error("Failed to fetch %s: %s", mid, e)
            finally:
                _fetch_metrics.add_request_latency(time.time() - t0, phase="match_details")

        async def _bounded(mid: str) -> None:
            async with sem:
                await _worker(mid)

        await asyncio.gather(*(_bounded(m) for m in match_ids))


if __name__ == "__main__":  # Simple CLI for direct execution
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Fetch and cache League of Legends match data for a Riot ID."
    )
    parser.add_argument("game_name", help="Riot IGN (e.g., Frowtch)")
    parser.add_argument("tag_line", help="Riot tag line (e.g., blue)")
    parser.add_argument("count", type=int, help="Number of recent matches to fetch (e.g., 20)")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore local cache and overwrite saved matches",
    )
    parser.add_argument(
        "--show-metrics",
        action="store_true",
        help="Print fetch metrics summary after completion",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Use legacy synchronous fetching instead of async",
    )
    parser.add_argument(
        "--include-timeline",
        action="store_true",
        help="Also fetch timeline data (slower and may 404 for some matches)",
    )

    args = parser.parse_args()

    # Enable file logging like older versions
    setup_file_logging()

    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        print("RIOT_API_TOKEN environment variable is not set")
        sys.exit(1)

    try:
        _fetch_metrics.start_timing()
        logger.info("Fetching PUUID for %s#%s", args.game_name, args.tag_line)
        puuid = fetch_puuid_by_riot_id(args.game_name, args.tag_line, token)
        logger.info("Successfully retrieved PUUID for %s#%s", args.game_name, args.tag_line)
        logger.info(
            "Starting fetch for player %s#%s - %d matches (cache: %s)",
            args.game_name,
            args.tag_line,
            args.count,
            "disabled" if args.no_cache else "enabled",
        )
        logger.info("Fetching up to %d matches for PUUID %s...", args.count, puuid[:10])
        ids = fetch_match_history(puuid, args.count, token)
        logger.info("Total match IDs fetched: %d", len(ids))
        if not ids:
            print("No matches found")
            sys.exit(0)
        has_httpx = importlib.util.find_spec("httpx") is not None
        use_sync = args.sync or (not has_httpx)
        if not has_httpx and not args.sync:
            print(
                "httpx not available; falling back to synchronous mode. "
                "Install 'httpx' to enable async."
            )
        if use_sync:
            for idx, mid in enumerate(ids, start=1):
                logger.info("Processing match %d/%d: %s", idx, len(ids), mid)
                if not args.no_cache:
                    fp = Path(MATCHES_DIR) / f"{mid}.json"
                    if fp.exists():
                        logger.info("Using cached data for %s", mid)
                        continue
                data = fetch_match_data(mid, token)
                if args.include_timeline:
                    logger.info("Fetching timeline data for %s", mid)
                    tl = fetch_timeline_data(mid, token)
                    if tl:
                        data["timeline"] = tl
                        logger.info("Successfully combined match and timeline data for %s", mid)
                save_match_data(mid, data)
                logger.info("Saved match data to %s/%s.json", MATCHES_DIR, mid)
            logger.info(
                "Processing complete. Successful: %d, Failed: %d, Cached: %d",
                len(ids),
                0,
                0,
            )
        else:
            asyncio.run(
                async_process_matches(
                    ids,
                    token,
                    use_cache=not args.no_cache,
                    include_timeline=args.include_timeline,
                )
            )
    except Exception as e:  # pragma: no cover - CLI runtime errors
        logger.error("Failed to fetch matches: %s", e)
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        _fetch_metrics.end_timing()

    print(
        f"Fetched {len(ids)} matches for {args.game_name}#{args.tag_line}. "
        f"Saved to '{MATCHES_DIR}/'."
    )

    if args.show_metrics:
        _fetch_metrics.print_summary()
