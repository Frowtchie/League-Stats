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

# Constants
MATCHES_DIR = "matches"
API_BASE_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/"
MATCH_HISTORY_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('league_stats.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_player_config() -> Dict[str, str]:
    """
    Load player PUUIDs from environment variables or config file.
    
    Returns:
        Dict[str, str]: Dictionary mapping player names to PUUIDs
    """
    # Try to load from environment variables first
    puuids = {}
    
    # Check for individual environment variables
    for player in ['Frowtch', 'Overowser', 'Suro']:
        env_var = f"PUUID_{player.upper()}"
        puuid = os.getenv(env_var)
        if puuid:
            puuids[player] = puuid
    
    # If no environment variables found, fall back to default values
    # (These should be moved to environment variables in production)
    if not puuids:
        logger.warning("No PUUID environment variables found. Using default values.")
        puuids = {
            "Frowtch": "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ",
            "Overowser": "yu20wMq06LlCyzvkfIn5K2Emx2n_urKtJuiJob6Oxtq-fRUGiuY9VRtHVg8NCtwBO9tauLLclW8TMA",
            "Suro": "oISoER4IhzrXfUtt--Sh0Vg9lVlitiVTKXDgngIRlCVgY4oDiufwqQjb4f7dmIRQzlL-4bmtOJxl7Q",
        }
    
    return puuids


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
                data = fetch_match_data(match_id, token)
                save_match_data(match_id, data)
                
            successful += 1
        except Exception as e:
            logger.error(f"Error processing match {match_id}: {e}")
            failed += 1
    
    logger.info(f"Processing complete. Successful: {successful}, Failed: {failed}, Cached: {cached}")


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
    if count > 100:
        logger.warning(f"Count {count} exceeds API limit of 100, limiting to 100")
        count = 100
        
    headers = {"X-Riot-Token": token}
    url = f"{MATCH_HISTORY_URL}{puuid}/ids?start=0&count={count}"
    
    try:
        logger.info(f"Fetching match history for PUUID {puuid[:10]}... (count: {count})")
        response = make_api_request(url, headers)
        match_ids = response.json()
        
        # Validate response
        if not isinstance(match_ids, list):
            raise ValueError("Expected list of match IDs, got different format")
            
        logger.info(f"Retrieved {len(match_ids)} match IDs")
        return match_ids
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match history: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse or validate JSON response for match history: {e}")
        raise


def main():
    """
    Main function to fetch and save match data.
    """
    parser = argparse.ArgumentParser(description="Fetch match data for a player.")
    parser.add_argument("player", type=str, help="The player's name (e.g., Frowtch).")
    parser.add_argument("count", type=int, help="The number of matches to fetch.")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set the logging level")
    parser.add_argument("--no-cache", action="store_true",
                       help="Disable caching and re-fetch all matches")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Get API token
    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        logger.error("RIOT_API_TOKEN environment variable is not set.")
        raise EnvironmentError("RIOT_API_TOKEN environment variable is not set.")

    # Load player configuration
    puuids = load_player_config()
    
    player = args.player
    count = args.count

    if player not in puuids:
        available_players = ", ".join(puuids.keys())
        logger.error(f"Player '{player}' not found. Available players: {available_players}")
        raise ValueError(f"Player '{player}' not found in PUUIDS. Available: {available_players}")

    puuid = puuids[player]
    use_cache = not args.no_cache
    
    logger.info(f"Starting fetch for player {player} - {count} matches (cache: {'enabled' if use_cache else 'disabled'})")
    
    try:
        match_ids = fetch_match_history(puuid, count, token)
        process_matches(match_ids, token, use_cache)
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise


if __name__ == "__main__":
    main()


def fetch_match_history(puuid: str, count: int, token: str) -> List[str]:
    """
    Fetches the match history for a player using requests library.

    Args:
        puuid (str): The player's PUUID.
        count (int): The number of matches to fetch.
        token (str): The API token for authentication.

    Returns:
        List[str]: A list of match IDs.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the response cannot be parsed as JSON.
    """
    headers = {"X-Riot-Token": token}
    url = f"{MATCH_HISTORY_URL}{puuid}/ids?start=0&count={count}"
    
    try:
        logger.info(f"Fetching match history for PUUID {puuid[:10]}... (count: {count})")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        match_ids = response.json()
        logger.info(f"Retrieved {len(match_ids)} match IDs")
        return match_ids
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch match history: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON response for match history: {e}")
        raise


def main():
    """
    Main function to fetch and save match data.
    """
    parser = argparse.ArgumentParser(description="Fetch match data for a player.")
    parser.add_argument("player", type=str, help="The player's name (e.g., Frowtch).")
    parser.add_argument("count", type=int, help="The number of matches to fetch.")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set the logging level")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Get API token
    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        logger.error("RIOT_API_TOKEN environment variable is not set.")
        raise EnvironmentError("RIOT_API_TOKEN environment variable is not set.")

    # Load player configuration
    puuids = load_player_config()
    
    player = args.player
    count = args.count

    if player not in puuids:
        available_players = ", ".join(puuids.keys())
        logger.error(f"Player '{player}' not found. Available players: {available_players}")
        raise ValueError(f"Player '{player}' not found in PUUIDS. Available: {available_players}")

    puuid = puuids[player]
    logger.info(f"Starting fetch for player {player} - {count} matches")
    
    try:
        match_ids = fetch_match_history(puuid, count, token)
        process_matches(match_ids, token)
        logger.info("Process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise


if __name__ == "__main__":
    main()