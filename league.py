def ensure_matches_for_player(
    puuid: str,
    token: str,
    matches_dir: str = "matches",
    min_matches: int = 1,
    fetch_count: int = 10,
) -> int:
    """
    Ensure there are at least `min_matches` match files for the given player in the directory.
    If not, fetch up to `fetch_count` matches and save them.

    Args:
        puuid (str): Player's PUUID
        token (str): Riot API token
        matches_dir (str): Directory to store match files
        min_matches (int): Minimum number of matches required
        fetch_count (int): Number of matches to fetch if needed

    Returns:
        int: Number of match files now present for the player
    """
    from pathlib import Path
    import glob

    matches_path = Path(matches_dir)
    matches_path.mkdir(exist_ok=True)
    # Count files containing this puuid (or just count all if not filtering by puuid)
    match_files = list(matches_path.glob("*.json"))
    player_match_count = 0
    for file in match_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Check if player is in this match
            if any(
                p.get("puuid") == puuid
                for p in data.get("info", {}).get("participants", [])
            ):
                player_match_count += 1
        except Exception:
            continue
    if player_match_count >= min_matches:
        return player_match_count
    # Fetch and save matches
    logger.info(
        f"No or not enough matches found for player {puuid[:10]}. Fetching {fetch_count} matches..."
    )
    match_ids = fetch_match_history(puuid, fetch_count, token)
    process_matches(match_ids, token, use_cache=False)
    # Recount
    match_files = list(matches_path.glob("*.json"))
    player_match_count = 0
    for file in match_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if any(
                p.get("puuid") == puuid
                for p in data.get("info", {}).get("participants", [])
            ):
                player_match_count += 1
        except Exception:
            continue
    return player_match_count


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetches data from the Riot Games API for a list of matches and saves the data as JSON files.
-----------------------------------------------------------------
Author: Frowtch
License: MPL 2.0
Version: 1.1.0
Maintainer: Frowtch
Contact: Frowtch#0001 on Discord
Status: Production
"""


import json
import os
import argparse
import logging
import sys
import time
from typing import List, Dict, Optional
import requests
from pathlib import Path

# Load environment variables from config.env if present
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

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
        logging.FileHandler("league_stats.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def make_api_request(url: str, headers: Dict[str, str], timeout: int = 30):
    """
    Make a request to the API with proper error handling.

    Args:
        url (str): The URL to request
        headers (Dict[str, str]): Request headers
        timeout (int): Request timeout in seconds

    Returns:
        requests.Response: The response object

    Raises:
        requests.RequestException: If the request fails
    """
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response


def validate_match_data(data: Dict) -> bool:
    """
    Validate that match data has the expected structure.

    Args:
        data (Dict): The match data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

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
            "No PUUID environment variables found. Will fetch PUUIDs from Riot API as needed."
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
        response = make_api_request(url, headers)
        data = response.json()

        # Validate response
        if not isinstance(data, dict) or "puuid" not in data:
            raise ValueError("Invalid response format - missing PUUID")

        puuid = data["puuid"]
        logger.info(f"Successfully retrieved PUUID for {game_name}#{tag_line}")
        return puuid

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Player '{game_name}#{tag_line}' not found")
        else:
            logger.error(f"HTTP error fetching PUUID: {e}")
            raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch PUUID for {game_name}#{tag_line}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse PUUID response: {e}")
        raise


def fetch_match_data(match_id: str, token: str) -> Dict:
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
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for match {match_id}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON response for match {match_id}: {e}")
        raise


def fetch_timeline_data(match_id: str, token: str) -> Optional[Dict]:
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
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch timeline data for match {match_id}: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Failed to parse timeline JSON response for match {match_id}: {e}")
        return None


def fetch_match_with_timeline(match_id: str, token: str) -> Dict:
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
        match_data['timeline'] = timeline_data
        logger.info(f"Successfully combined match and timeline data for {match_id}")
    else:
        logger.info(f"Timeline data not available for {match_id}, proceeding with match data only")
    
    return match_data


def save_match_data(match_id: str, data: Dict) -> None:
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


def load_cached_match_data(match_id: str) -> Optional[Dict]:
    """
    Loads cached match data from a JSON file if it exists.

    Args:
        match_id (str): The match ID to load

    Returns:
        Optional[Dict]: The cached match data, or None if not found/invalid
    """
    file_path = Path(MATCHES_DIR) / f"{match_id}.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Validate cached data
        if validate_match_data(data):
            logger.debug(f"Loaded cached match data for {match_id}")
            return data
        else:
            logger.warning(f"Cached data for {match_id} is invalid, will re-fetch")
            return None

    except (IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load cached data for {match_id}: {e}")
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
    all_match_ids = []
    start = 0
    remaining = count
    max_per_request = 100

    logger.info(f"Fetching up to {count} matches for PUUID {puuid[:10]}...")
    while remaining > 0:
        batch_count = min(max_per_request, remaining)
        url = f"{MATCH_HISTORY_URL}{puuid}/ids?start={start}&count={batch_count}"
        try:
            response = make_api_request(url, headers)
            match_ids = response.json()
            if not isinstance(match_ids, list):
                raise ValueError("Expected list of match IDs, got different format")
            all_match_ids.extend(match_ids)
            logger.info(
                f"Fetched {len(match_ids)} match IDs (start={start}, count={batch_count})"
            )
            if len(match_ids) < batch_count:
                # No more matches available
                break
            start += batch_count
            remaining -= batch_count
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "2"))
                logger.warning(
                    f"Rate limit hit (429). Sleeping for {retry_after} seconds..."
                )
                import time

                time.sleep(retry_after)
                continue
            else:
                logger.error(f"Failed to fetch match history: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch match history: {e}")
            raise
        except ValueError as e:
            logger.error(
                f"Failed to parse or validate JSON response for match history: {e}"
            )
            raise

    logger.info(f"Total match IDs fetched: {len(all_match_ids)}")
    return all_match_ids


def main():
    """
    Main function to fetch and save match data.
    """
    parser = argparse.ArgumentParser(
        description="Fetch match data for a player by Riot ID."
    )
    parser.add_argument(
        "game_name", type=str, help="The player's game name (e.g., Frowtch)."
    )
    parser.add_argument(
        "tag_line", type=str, help="The player's tag line (e.g., blue)."
    )
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
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Get API token
    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        logger.error("RIOT_API_TOKEN environment variable is not set.")
        raise EnvironmentError("RIOT_API_TOKEN environment variable is not set.")

    # Fetch PUUID dynamically using Riot ID
    game_name = args.game_name
    tag_line = args.tag_line
    count = args.count
    use_cache = not args.no_cache

    try:
        puuid = fetch_puuid_by_riot_id(game_name, tag_line, token)
        logger.info(
            f"Starting fetch for player {game_name}#{tag_line} - {count} matches (cache: {'enabled' if use_cache else 'disabled'})"
        )

        match_ids = fetch_match_history(puuid, count, token)
        process_matches(match_ids, token, use_cache)
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise


if __name__ == "__main__":
    main()
