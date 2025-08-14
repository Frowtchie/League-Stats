#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetches data from the Riot Games API for a list of matches and saves the data as JSON files.
-----------------------------------------------------------------
Author: Frowtch
License: MPL 2.0
Version: 1.0.0
Maintainer: Frowtch
Contact: Frowtch#0001 on Discord
Status: WIP
"""

import subprocess
import json
import os
import argparse
from typing import List, Dict

# Constants
MATCHES_DIR = "matches"
API_BASE_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/"
HEADERS_TEMPLATE = {"X-Riot-Token": "{token}"}

# Player PUUIDs
PUUIDS = {
    "Frowtch": "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ",
    "Overowser": "yu20wMq06LlCyzvkfIn5K2Emx2n_urKtJuiJob6Oxtq-fRUGiuY9VRtHVg8NCtwBO9tauLLclW8TMA",
    "Suro": "oISoER4IhzrXfUtt--Sh0Vg9lVlitiVTKXDgngIRlCVgY4oDiufwqQjb4f7dmIRQzlL-4bmtOJxl7Q",
}


def fetch_match_data(match_id: str, token: str) -> Dict:
    """
    Fetches match data from the Riot Games API.

    Args:
        match_id (str): The match ID to fetch data for.
        token (str): The API token for authentication.

    Returns:
        Dict: The match data as a dictionary.
    """
    headers = {"X-Riot-Token": token}
    url = f"{API_BASE_URL}{match_id}"
    result = subprocess.run(
        ["curl", "-s", "-H", f"X-Riot-Token: {token}", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to fetch data for match {match_id}: {result.stderr}"
        )
    return json.loads(result.stdout)


def save_match_data(match_id: str, data: Dict) -> None:
    """
    Saves match data to a JSON file.

    Args:
        match_id (str): The match ID to use as the filename.
        data (Dict): The match data to save.
    """
    os.makedirs(MATCHES_DIR, exist_ok=True)
    file_path = os.path.join(MATCHES_DIR, f"{match_id}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print(f"Saved match data to {file_path}")


def process_matches(match_ids: List[str], token: str) -> None:
    """
    Processes a list of match IDs by fetching and saving their data.

    Args:
        match_ids (List[str]): A list of match IDs to process.
        token (str): The API token for authentication.
    """
    for match_id in match_ids:
        try:
            print(f"Fetching data for match {match_id}...")
            data = fetch_match_data(match_id, token)
            save_match_data(match_id, data)
        except Exception as e:
            print(f"Error processing match {match_id}: {e}")


def fetch_match_history(puuid: str, count: int, token: str) -> List[str]:
    """
    Fetches the match history for a player.

    Args:
        puuid (str): The player's PUUID.
        count (int): The number of matches to fetch.
        token (str): The API token for authentication.

    Returns:
        List[str]: A list of match IDs.
    """
    headers = {"X-Riot-Token": token}
    url = f"{API_BASE_URL}by-puuid/{puuid}/ids?start=0&count={count}"
    result = subprocess.run(
        ["curl", "-s", "-H", f"X-Riot-Token: {token}", url],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch match history: {result.stderr}")
    return json.loads(result.stdout)


def main():
    """
    Main function to fetch and save match data.
    """
    parser = argparse.ArgumentParser(description="Fetch match data for a player.")
    parser.add_argument("player", type=str, help="The player's name (e.g., Frowtch).")
    parser.add_argument("count", type=int, help="The number of matches to fetch.")
    args = parser.parse_args()

    token = os.getenv("RIOT_API_TOKEN")
    if not token:
        raise EnvironmentError("RIOT_API_TOKEN environment variable is not set.")

    player = args.player
    count = args.count

    if player not in PUUIDS:
        raise ValueError(f"Player '{player}' not found in PUUIDS.")

    puuid = PUUIDS[player]
    print(f"Fetching the last {count} matches for player {player}...")
    try:
        match_ids = fetch_match_history(puuid, count, token)
        process_matches(match_ids, token)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
