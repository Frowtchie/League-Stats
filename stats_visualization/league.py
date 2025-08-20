"""League match data fetcher.

Fetches data from the Riot Games API for a list of matches and saves the data as JSON files.
-----------------------------------------------------------------
Author: Frowtch
License: MPL 2.0
Version: 0.4.0  # Keep in sync with stats_visualization/__init__.py and pyproject.toml
Maintainer: Frowtch
Contact: Frowtch#0001 on Discord
Status: Production
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import requests
from dotenv import load_dotenv

# Load environment variables from config.env if present
load_dotenv(dotenv_path="config.env")


@dataclass
class FetchMetrics:
    """Metrics collected during match fetching operations."""

    # Timing metrics
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    retry_count: int = 0

    # Latency tracking (in seconds)
    request_latencies: List[float] = field(default_factory=list)

    # Per-phase breakdown
    match_ids_requests: int = 0
    match_details_requests: int = 0
    timeline_requests: int = 0

    # Timing for major phases
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def add_request_latency(self, latency: float, request_type: str = "unknown") -> None:
        """Add a request latency measurement."""
        self.request_latencies.append(latency)
        self.total_requests += 1

        if request_type == "match_ids":
            self.match_ids_requests += 1
        elif request_type == "match_details":
            self.match_details_requests += 1
        elif request_type == "timeline":
            self.timeline_requests += 1

    def add_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def add_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    def add_retry(self) -> None:
        """Record a retry attempt."""
        self.retry_count += 1

    def start_timing(self) -> None:
        """Start timing the overall operation."""
        self.start_time = time.time()

    def end_timing(self) -> None:
        """End timing the overall operation."""
        self.end_time = time.time()

    @property
    def total_duration(self) -> Optional[float]:
        """Get total operation duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def avg_latency(self) -> float:
        """Get average request latency in seconds."""
        if not self.request_latencies:
            return 0.0
        return sum(self.request_latencies) / len(self.request_latencies)

    @property
    def p95_latency(self) -> float:
        """Get 95th percentile latency in seconds."""
        if not self.request_latencies:
            return 0.0
        sorted_latencies = sorted(self.request_latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def max_latency(self) -> float:
        """Get maximum latency in seconds."""
        if not self.request_latencies:
            return 0.0
        return max(self.request_latencies)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON export."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "retry_count": self.retry_count,
            "avg_latency_ms": self.avg_latency * 1000,
            "p95_latency_ms": self.p95_latency * 1000,
            "max_latency_ms": self.max_latency * 1000,
            "total_duration_seconds": self.total_duration,
            "phase_breakdown": {
                "match_ids_requests": self.match_ids_requests,
                "match_details_requests": self.match_details_requests,
                "timeline_requests": self.timeline_requests,
            },
        }

    def print_summary(self) -> None:
        """Print a summary of metrics to console."""
        print("=== Fetch Metrics Summary ===")
        print(f"Total requests: {self.total_requests}")
        print(f"Cache hits: {self.cache_hits}, Cache misses: {self.cache_misses}")
        if self.total_requests > 0:
            cache_ratio = (
                self.cache_hits / (self.cache_hits + self.cache_misses) * 100
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            )
            print(f"Cache hit ratio: {cache_ratio:.1f}%")
        print(f"Retry count: {self.retry_count}")
        if self.request_latencies:
            print(
                f"Latency - Avg: {self.avg_latency * 1000:.1f}ms, "
                f"P95: {self.p95_latency * 1000:.1f}ms, "
                f"Max: {self.max_latency * 1000:.1f}ms"
            )
        if self.total_duration:
            print(f"Total duration: {self.total_duration:.2f}s")
        print(
            f"Phase breakdown - IDs: {self.match_ids_requests}, "
            f"Details: {self.match_details_requests}, "
            f"Timelines: {self.timeline_requests}"
        )
        print("=============================")


# Global metrics instance
_fetch_metrics = FetchMetrics()


def ensure_matches_for_player(
    puuid: str,
    token: str,
    matches_dir: str = "matches",
    min_matches: int = 1,
    fetch_count: int = 10,
) -> int:
    """Ensure at least ``min_matches`` for the given player exist locally.

    If fewer than ``min_matches`` are present, fetch up to ``fetch_count`` new
    matches (uncached) and then recount.
    """

    matches_path = Path(matches_dir)
    matches_path.mkdir(exist_ok=True)

    def _count_player_matches() -> int:
        count = 0
        for file in matches_path.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if any(
                    p.get("puuid") == puuid for p in data.get("info", {}).get("participants", [])
                ):
                    count += 1
            except Exception:  # pragma: no cover - defensive
                continue
        return count

    player_match_count = _count_player_matches()
    if player_match_count >= min_matches:
        return player_match_count

    logger.info(
        "No or not enough matches found for player %s. Fetching %d matches...",
        puuid[:10],
        fetch_count,
    )
    match_ids = fetch_match_history(puuid, fetch_count, token)
    process_matches(match_ids, token, use_cache=False)
    return _count_player_matches()


# Constants
MATCHES_DIR = "matches"
API_BASE_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/"
TIMELINE_API_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
MATCH_HISTORY_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/"


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/league_stats.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Module-level logger for this file
logger = logging.getLogger(__name__)


def make_api_request(
    url: str, headers: Dict[str, str], timeout: int = 30, request_type: str = "unknown"
):
    """
    Make a request to the API with proper error handling and metrics collection.

    Args:
        url (str): The URL to request
        headers (Dict[str, str]): Request headers
        timeout (int): Request timeout in seconds
        request_type (str): Type of request for metrics tracking

    Returns:
        requests.Response: The response object

    Raises:
        requests.RequestException: If the request fails
    """
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, request_type)
        return response
    except requests.exceptions.HTTPError as e:
        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, request_type)
        if e.response is not None and e.response.status_code == 429:
            _fetch_metrics.add_retry()
        raise
    except Exception:
        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, request_type)
        raise


def validate_match_data(data: Dict[str, Any]) -> bool:
    """
    Validate that match data has the expected structure.

    Args:
        data (Dict): The match data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Dict[str, Any] is always a dict, so skip isinstance check

    # Check for required fields
    required_fields = ["info", "metadata"]
    return all(field in data for field in required_fields)


def load_player_config() -> Dict[str, str]:
    """
    Load player PUUIDs from environment variables or config file.

    Returns:
        Dict[str, str]: Dictionary mapping player names to PUUIDs
    """
    # Try to load from environment variables first
    puuids = {}

    # Check for individual environment variables
    for player in ["Frowtch", "Overowser", "Suro"]:
        env_var = f"PUUID_{player.upper()}"
        puuid = os.getenv(env_var)
        if puuid:
            puuids[player] = puuid

    # If no environment variables found, fall back to default values
    # (These should be moved to environment variables in production)
    if not puuids:
        logger.warning(
            "No PUUID environment variables found. " "Will fetch PUUIDs from Riot API as needed."
        )
        puuids = {
            "Frowtch": "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ",
            "Overowser": "yu20wMq06LlCyzvkfIn5K2Emx2n_urKtJuiJob6Oxtq-fRUGiuY9VRtHVg8NCtwBO9tauLLclW8TMA",
            "Suro": "oISoER4IhzrXfUtt--Sh0Vg9lVlitiVTKXDgngIRlCVgY4oDiufwqQjb4f7dmIRQzlL-4bmtOJxl7Q",
        }

    return puuids


def fetch_puuid_by_riot_id(game_name: str, tag_line: str, token: str) -> str:
    """
    Fetch PUUID for a player using their Riot ID (game name + tag line).

    Args:
        game_name (str): The player's game name (e.g., "Frowtch")
        tag_line (str): The player's tag line (e.g., "blue")
        token (str): The API token for authentication

    Returns:
        str: The player's PUUID

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If the player is not found or response is invalid
    """
    # Use the Americas endpoint for account data (covers NA, BR, LAN, LAS, OCE)
    # For other regions, you might need to use different endpoints:
    # - asia.api.riotgames.com (for KR, JP, etc.)
    # - europe.api.riotgames.com (for EUW, EUNE, TR, RU)
    base_url = "https://americas.api.riotgames.com"
    url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": token}

    try:
        logger.info(f"Fetching PUUID for {game_name}#{tag_line}")
        response = make_api_request(url, headers, timeout=30, request_type="puuid")
        data = response.json()

        if not isinstance(data, dict) or "puuid" not in data:
            raise ValueError("Invalid response format - missing PUUID")

        from typing import cast

        puuid = cast(str, data["puuid"])  # ensure str type
        logger.info(f"Successfully retrieved PUUID for {game_name}#{tag_line}")
        return puuid
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise ValueError(f"Player '{game_name}#{tag_line}' not found")
        logger.error(f"HTTP error fetching PUUID: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch PUUID for {game_name}#{tag_line}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse PUUID response: {e}")
        raise


def fetch_match_data(match_id: str, token: str) -> Dict[str, Any]:
    """
    Fetches match data from the Riot Games API using requests library.

    Args:
        match_id (str): The match ID to fetch data for.
        token (str): The API token for authentication.

    Returns:
        Dict: The match data as a dictionary.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the response cannot be parsed as JSON.
    """
    headers = {"X-Riot-Token": token}
    url = f"{API_BASE_URL}{match_id}"

    try:
        logger.info(f"Fetching match data for {match_id}")
        response = make_api_request(url, headers, timeout=30, request_type="match_details")
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Match data response was not an object")
        return cast(Dict[str, Any], data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for match {match_id}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON response for match {match_id}: {e}")
        raise


def fetch_timeline_data(match_id: str, token: str) -> Optional[Dict[str, Any]]:
    """
    Fetches timeline data for a match from the Riot Games API.

    Args:
        match_id (str): The match ID to fetch timeline data for.
        token (str): The API token for authentication.

    Returns:
        Optional[Dict]: The timeline data as a dictionary, or None if failed.
    """
    headers = {"X-Riot-Token": token}
    url = TIMELINE_API_URL.format(match_id=match_id)

    try:
        logger.info(f"Fetching timeline data for {match_id}")
        response = make_api_request(url, headers, timeout=30, request_type="timeline")
        data = response.json()
        if not isinstance(data, dict):
            return None
        return cast(Dict[str, Any], data)
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch timeline data for match {match_id}: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Failed to parse timeline JSON response for match {match_id}: {e}")
        return None


def fetch_match_with_timeline(match_id: str, token: str) -> Dict[str, Any]:
    """
    Fetches both match data and timeline data, combining them into a single response.

    Args:
        match_id (str): The match ID to fetch data for.
        token (str): The API token for authentication.

    Returns:
        Dict: Combined match data with timeline included.
    """
    # Fetch main match data
    match_data = fetch_match_data(match_id, token)
    # Fetch timeline data (optional, don't fail if it's not available)
    timeline_data = fetch_timeline_data(match_id, token)

    # Combine the data
    if timeline_data:
        match_data["timeline"] = timeline_data
        logger.info(f"Successfully combined match and timeline data for {match_id}")
    else:
        logger.info(f"Timeline data not available for {match_id}, proceeding with match data only")

    return match_data


def save_match_data(match_id: str, data: Dict[str, Any]) -> None:
    """
    Saves match data to a JSON file.

    Args:
        match_id (str): The match ID to use as the filename.
        data (Dict): The match data to save.
    """
    Path(MATCHES_DIR).mkdir(exist_ok=True)
    file_path = Path(MATCHES_DIR) / f"{match_id}.json"

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logger.info(f"Saved match data to {file_path}")
    except IOError as e:
        logger.error(f"Failed to save match data to {file_path}: {e}")
        raise


def load_cached_match_data(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Loads cached match data from a JSON file if it exists.

    Args:
        match_id (str): The match ID to load

    Returns:
        Optional[Dict]: The cached match data, or None if not found/invalid
    """
    file_path = Path(MATCHES_DIR) / f"{match_id}.json"

    if not file_path.exists():
        _fetch_metrics.add_cache_miss()
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
            data = cast(Dict[str, Any], loaded) if isinstance(loaded, dict) else {}

        # Validate cached data
        if validate_match_data(data):
            logger.debug(f"Loaded cached match data for {match_id}")
            _fetch_metrics.add_cache_hit()
            return data
        else:
            logger.warning(f"Cached data for {match_id} is invalid, will re-fetch")
            _fetch_metrics.add_cache_miss()
            return None

    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load cached data for {match_id}: {e}")
        _fetch_metrics.add_cache_miss()
        return None


def process_matches(match_ids: List[str], token: str, use_cache: bool = True) -> None:
    """
    Processes a list of match IDs by fetching and saving their data.

    Args:
        match_ids (List[str]): A list of match IDs to process.
        token (str): The API token for authentication.
        use_cache (bool): Whether to use cached data if available.
    """
    total_matches = len(match_ids)
    successful = 0
    failed = 0
    cached = 0

    for i, match_id in enumerate(match_ids, 1):
        try:
            logger.info(f"Processing match {i}/{total_matches}: {match_id}")

            # Try to load from cache first
            data = None
            if use_cache:
                data = load_cached_match_data(match_id)
                if data:
                    cached += 1
                    logger.info(f"Using cached data for {match_id}")

            # Fetch from API if not cached or cache disabled
            if data is None:
                data = fetch_match_with_timeline(match_id, token)
                save_match_data(match_id, data)

            successful += 1
        except Exception as e:
            logger.error(f"Error processing match {match_id}: {e}")
            failed += 1

    logger.info(
        f"Processing complete. Successful: {successful}, Failed: {failed}, Cached: {cached}"
    )


def fetch_match_history(puuid: str, count: int, token: str) -> List[str]:
    """
    Fetches the match history for a player using requests library with rate limiting.

    Args:
        puuid (str): The player's PUUID.
        count (int): The number of matches to fetch (max 100 per API limits).
        token (str): The API token for authentication.

    Returns:
        List[str]: A list of match IDs.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the response cannot be parsed as JSON or count is invalid.
    """
    # Validate input parameters
    if count <= 0:
        raise ValueError("Count must be positive")

    headers = {"X-Riot-Token": token}
    all_match_ids: List[str] = []
    start = 0
    remaining = count
    max_per_request = 100

    logger.info(f"Fetching up to {count} matches for PUUID {puuid[:10]}...")
    while remaining > 0:
        batch_count = min(max_per_request, remaining)
        url = f"{MATCH_HISTORY_URL}{puuid}/ids?start={start}&count={batch_count}"
        try:
            response = make_api_request(url, headers, timeout=30, request_type="match_ids")
            raw_ids_any = response.json()
            if not isinstance(raw_ids_any, list):
                raise ValueError("Match history response was not a list")
            raw_ids: List[object] = list(raw_ids_any)
            raw_ids_filtered: List[object] = [mid for mid in raw_ids if isinstance(mid, (str, int))]
            batch_ids: List[str] = [str(mid) for mid in raw_ids_filtered]
            all_match_ids.extend(batch_ids)
            logger.info(f"Fetched {len(batch_ids)} match IDs (start={start}, count={batch_count})")
            if len(batch_ids) < batch_count:
                # No more matches available
                break
            start += batch_count
            remaining -= batch_count
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "2"))
                logger.warning(f"Rate limit hit (429). Sleeping for {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"Failed to fetch match history: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch match history: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse or validate JSON response for match history: {e}")
            raise

    logger.info(f"Total match IDs fetched: {len(all_match_ids)}")
    return all_match_ids


def export_metrics_json(filepath: str) -> None:
    """
    Export metrics to a JSON file.

    Args:
        filepath (str): Path to the JSON file to export metrics to
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(_fetch_metrics.to_dict(), f, indent=2)
        logger.info(f"Metrics exported to {filepath}")
    except IOError as e:
        logger.error(f"Failed to export metrics to {filepath}: {e}")


async def process_matches_async(
    match_ids: List[str], token: str, use_cache: bool = True, concurrency: int = 5
) -> None:
    """
    Processes a list of match IDs asynchronously with concurrency control.

    Args:
        match_ids (List[str]): A list of match IDs to process.
        token (str): The API token for authentication.
        use_cache (bool): Whether to use cached data if available.
        concurrency (int): Maximum number of concurrent requests.
    """
    try:
        import httpx
        import asyncio
    except ImportError:
        logger.error("httpx not available for async processing")
        raise

    successful = 0
    failed = 0
    cached = 0

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)

    async def process_single_match(match_id: str, session) -> bool:
        """Process a single match with concurrency control."""
        nonlocal successful, failed, cached

        async with semaphore:
            try:
                logger.info(f"Processing match: {match_id}")

                # Try to load from cache first
                data = None
                if use_cache:
                    data = load_cached_match_data(match_id)
                    if data:
                        cached += 1
                        logger.info(f"Using cached data for {match_id}")

                # Fetch from API if not cached or cache disabled
                if data is None:
                    data = await fetch_match_with_timeline_async(match_id, token, session)
                    save_match_data(match_id, data)

                successful += 1
                return True
            except Exception as e:
                logger.error(f"Error processing match {match_id}: {e}")
                failed += 1
                return False

    # Create async HTTP client
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Process all matches concurrently
        tasks = [process_single_match(match_id, client) for match_id in match_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(
        f"Async processing complete. Successful: {successful}, Failed: {failed}, Cached: {cached}"
    )


async def fetch_match_with_timeline_async(match_id: str, token: str, session) -> Dict[str, Any]:
    """
    Asynchronously fetches both match data and timeline data, combining them into a single response.

    Args:
        match_id (str): The match ID to fetch data for.
        token (str): The API token for authentication.
        session: The async HTTP client session.

    Returns:
        Dict: Combined match data with timeline included.
    """
    import asyncio  # Import here to ensure availability

    # Fetch both match and timeline data concurrently
    match_task = fetch_match_data_async(match_id, token, session)
    timeline_task = fetch_timeline_data_async(match_id, token, session)

    match_data, timeline_data = await asyncio.gather(
        match_task, timeline_task, return_exceptions=True
    )

    # Handle exceptions
    if isinstance(match_data, Exception):
        raise match_data

    # Timeline data is optional, so we just log if it fails
    if isinstance(timeline_data, Exception):
        logger.warning(f"Failed to fetch timeline data for {match_id}: {timeline_data}")
        timeline_data = None

    # Combine the data
    if timeline_data:
        # Ensure correct typing for match_data before mutation
        assert isinstance(match_data, dict), "Expected dict from fetch_match_data_async"
        match_data = cast(Dict[str, Any], match_data)
        match_data["timeline"] = timeline_data
        logger.info(f"Successfully combined match and timeline data for {match_id}")
    else:
        logger.info(f"Timeline data not available for {match_id}, proceeding with match data only")

    # Ensure mypy understands the return type
    return cast(Dict[str, Any], match_data)


async def fetch_match_data_async(match_id: str, token: str, session) -> Dict[str, Any]:
    """
    Asynchronously fetches match data from the Riot Games API.

    Args:
        match_id (str): The match ID to fetch data for.
        token (str): The API token for authentication.
        session: The async HTTP client session.

    Returns:
        Dict: The match data as a dictionary.
    """
    import asyncio  # Import here to ensure availability

    headers = {"X-Riot-Token": token}
    url = f"{API_BASE_URL}{match_id}"

    start_time = time.time()
    try:
        logger.info(f"Async fetching match data for {match_id}")
        response = await session.get(url, headers=headers)
        await response.raise_for_status()

        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, "match_details")

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Match data response was not an object")
        return cast(Dict[str, Any], data)
    except Exception as e:
        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, "match_details")

        # Check if it's an HTTP status error
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            if e.response.status_code == 429:
                _fetch_metrics.add_retry()
                # Simple backoff for 429 errors
                retry_after = int(e.response.headers.get("Retry-After", "2"))
                logger.warning(
                    f"Rate limit hit (429) for {match_id}. Sleeping for {retry_after} seconds..."
                )
                await asyncio.sleep(retry_after)
                # Retry once
                return await fetch_match_data_async(match_id, token, session)

        logger.error(f"Failed to fetch data for match {match_id}: {e}")
        raise


async def fetch_timeline_data_async(match_id: str, token: str, session) -> Optional[Dict[str, Any]]:
    """
    Asynchronously fetches timeline data for a match from the Riot Games API.

    Args:
        match_id (str): The match ID to fetch timeline data for.
        token (str): The API token for authentication.
        session: The async HTTP client session.

    Returns:
        Optional[Dict]: The timeline data as a dictionary, or None if failed.
    """
    import asyncio  # Import here to ensure availability

    headers = {"X-Riot-Token": token}
    url = TIMELINE_API_URL.format(match_id=match_id)

    start_time = time.time()
    try:
        logger.info(f"Async fetching timeline data for {match_id}")
        response = await session.get(url, headers=headers)
        await response.raise_for_status()

        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, "timeline")

        data = response.json()
        if not isinstance(data, dict):
            return None
        return cast(Dict[str, Any], data)
    except Exception as e:
        latency = time.time() - start_time
        _fetch_metrics.add_request_latency(latency, "timeline")

        # Check if it's an HTTP status error
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            if e.response.status_code == 429:
                _fetch_metrics.add_retry()
                # Simple backoff for 429 errors
                retry_after = int(e.response.headers.get("Retry-After", "2"))
                logger.warning(
                    f"Rate limit hit (429) for timeline {match_id}. Sleeping for {retry_after} seconds..."
                )
                await asyncio.sleep(retry_after)
                # Retry once
                return await fetch_timeline_data_async(match_id, token, session)

        logger.warning(f"Failed to fetch timeline data for match {match_id}: {e}")
        return None


def main():
    """
    Main function to fetch and save match data.
    """
    parser = argparse.ArgumentParser(description="Fetch match data for a player by Riot ID.")
    parser.add_argument("game_name", type=str, help="The player's game name (e.g., Frowtch).")
    parser.add_argument("tag_line", type=str, help="The player's tag line (e.g., blue).")
    parser.add_argument("count", type=int, help="The number of matches to fetch.")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching and re-fetch all matches",
    )
    parser.add_argument(
        "--sync-mode",
        action="store_true",
        help="Use synchronous mode instead of default async/batched fetching",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help="Maximum concurrent requests when using async mode (default: 8)",
    )
    parser.add_argument(
        "--metrics-json",
        type=str,
        help="Export metrics to JSON file",
    )
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Get API token
    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        logger.error("RIOT_API_TOKEN environment variable is not set.")
        raise EnvironmentError("RIOT_API_TOKEN environment variable is not set.")

    # Check async mode availability - default to async unless explicitly disabled or httpx unavailable
    async_mode = not args.sync_mode
    if async_mode:
        try:
            import httpx  # noqa: F401
        except ImportError:
            logger.warning(
                "httpx not available, falling back to synchronous mode. Install with: pip install httpx"
            )
            async_mode = False

    # Fetch PUUID dynamically using Riot ID
    game_name = args.game_name
    tag_line = args.tag_line
    count = args.count
    use_cache = not args.no_cache

    # Initialize metrics timing
    _fetch_metrics.start_timing()

    try:
        puuid = fetch_puuid_by_riot_id(game_name, tag_line, token)
        logger.info(
            f"Starting fetch for player {game_name}#{tag_line} - {count} matches "
            f"(cache: {'enabled' if use_cache else 'disabled'}, "
            f"mode: {'async' if async_mode else 'sync'}"
            f"{f', concurrency: {args.concurrency}' if async_mode else ''})"
        )

        match_ids = fetch_match_history(puuid, count, token)

        if async_mode:
            # Use async processing
            import asyncio

            asyncio.run(process_matches_async(match_ids, token, use_cache, args.concurrency))
        else:
            # Use sync processing
            process_matches(match_ids, token, use_cache)

        _fetch_metrics.end_timing()

        # Print metrics summary if async mode was used or if explicitly requested
        if async_mode or args.metrics_json:
            _fetch_metrics.print_summary()

        # Export metrics to JSON if requested
        if args.metrics_json:
            export_metrics_json(args.metrics_json)

        logger.info("Process completed successfully")
    except Exception as e:
        _fetch_metrics.end_timing()
        logger.error(f"Process failed: {e}")
        raise


if __name__ == "__main__":
    main()
