#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This code is using the subprocess and json modules in Python to fetch data from the Riot Games API for a list of matches specified in the matches variable. It then saves the returned data as JSON files in a matches directory, using the match IDs as the filenames.
The code first imports the subprocess and json modules, which are used for running external commands (in this case, the curl command) and working with JSON data, respectively.
Next, it defines a list of match IDs to fetch data for and a token for authenticating with the API.
In the for loop, the code sets the headers for the curl command using the API token, and builds the URL for the API request using the current match ID. It then runs the curl command, decodes the output as a JSON string, and converts it to a Python object using the json.loads() function.
Finally, it saves the JSON object to a file in the matches directory using the json.dump() function, with indentation set to 4 spaces to make the output more readable.
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

puuid = {"Frowtch" : "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ",
        "Overowser" : "yu20wMq06LlCyzvkfIn5K2Emx2n_urKtJuiJob6Oxtq-fRUGiuY9VRtHVg8NCtwBO9tauLLclW8TMA",
        "Suro" : "oISoER4IhzrXfUtt--Sh0Vg9lVlitiVTKXDgngIRlCVgY4oDiufwqQjb4f7dmIRQzlL-4bmtOJxl7Q",
        "Salem" : "pM0TaxQR5yoNGHKuqM9b84Oy-72bLE0z3UF6V-7ehwUW8Gq_YKl9ipqnpIarQCO66tHaMmCyFj_FZw"
        }
token ='RGAPI-5687cee8-2d46-419a-89f4-c5615f299130'
headers = ['-H', 'Accept-Charset: application/x-www-form-urlencoded', '-H', 'Origin: https://developer.riotgames.com', '-H', 'X-Riot-Token: '+token]

def getMatchesByPuuid(puuid, number_of_games=20):
    """Get last X games IDs from a player's PUUID

    Args:
        puuid (str): a players PUUID, can be gotten from /lol/summoner/v4/summoners/by-name/{summonerName}
    """
    # Build the URL for the curl command
    url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0'

    # Specify number of matches (optional)
    if number_of_games != 20:
        url = url + '&count=' + str(number_of_games)

    # Run the curl command and save the output
    output = subprocess.run(['curl', '-s', url, *headers], stdout=subprocess.PIPE)

    # Decode the output as a string
    json_string = output.stdout.decode('utf-8')

    # Load the JSON string as a Python object
    matches = json.loads(json_string)

    return matches

def getMatchByMatchID(match_id):
    """Get match details from a match ID

    Args:
        matchId (str): ID of the match
    """
    # Build the URL for the curl command
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"

    # Run the curl command and save the output
    output = subprocess.run(['curl', '-s', url, *headers], stdout=subprocess.PIPE)

    # Decode the output as a string
    json_string = output.stdout.decode('utf-8')

    # Load the JSON string as a Python object
    match_details = json.loads(json_string)

    # Save the JSON object to a file
    with open(f'matches/{match_id}.json', 'w') as f:
        json.dump(match_details, f, indent=4)

def getMatchTimelineByMatchID(match_id):
    """Get match details from a match ID

    Args:
        matchId (str): ID of the match
    """
    # Build the URL for the curl command
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"

    # Run the curl command and save the output
    output = subprocess.run(['curl', '-s', url, *headers], stdout=subprocess.PIPE)

    # Decode the output as a string
    json_string = output.stdout.decode('utf-8')

    # Load the JSON string as a Python object
    match_details = json.loads(json_string)

    # Save the JSON object to a file
    with open(f'timelines/{match_id}.json', 'w') as f:
        json.dump(match_details, f, indent=4)

def extractPlayerData(match_id, puuid):
    """Extracts player specific data from match details

    Args:
        match_id (str): id of the match, also name of the file
        puuid (str): PUUID of player

    Returns:
        str: data specific to player with PUUID
    """
    # Open the JSON file
    with open(f'matches/{match_id}.json') as file:
        # Load the JSON data from the file
        json_data = json.load(file)
    for participant in json_data['info']['participants']:
        if participant['puuid'] == puuid:
            with open(f'data/{match_id}-data.json', 'w') as f:
                json.dump(participant, f, indent=4)

def getChampionTags(champion):
    """Returns the tags of a champion. Available tags are: ['Tank', 'Support', 'Marksman', 'Mage', 'Fighter', 'Assassin']

    Args:
        champion (str): name of a champion
    """
    tags = ''
    formatted_champion = champion.title()
    with open('champions.json') as file:
        json_data = json.load(file)
    for tag in json_data['data'][formatted_champion]['tags']:
        tags = tags + tag + ' '
    return tags

def analyseMatch(match_id):
    """Returns some key data from a player's match data file

    Args:
        match_id (str): the match ID
    Returns:
        result (str): Victory or Defeat
        Kills (str): number of kills
        Deaths (str): number of deaths
        Assists (str): number of assists
    """
    with open(f'data/{match_id}-data.json') as file:
        # Load the JSON data from the file
        json_data = json.load(file)
    champion_name = json_data['championName']
    if json_data['win'] == True:
        result = 'Victory'
    else:
        result = 'Defeat'
    kills = json_data['kills']
    deaths = json_data['deaths']
    assists = json_data['assists']
    return(champion_name, result, kills, deaths, assists)


if __name__ == '__main__' :
    wins = 0
    losses = 0
    matches = getMatchesByPuuid(puuid['Frowtch'], 50)
    for match in matches:
        # getMatchTimelineByMatchID(match)
        getMatchByMatchID(match)
        # extractPlayerData(match, puuid['Frowtch'])
        # data = analyseMatch(match)
        # # print(data[0] + ', tags: ' + getChampionTags(data[0]))
        # if data[0] == 'Thresh':
        #     print(data)
        #     if data[1] == 'Victory':
        #         wins = wins + 1
        #     else:
        #         losses = losses + 1
    # print('Winrate: ' + str((wins/(wins+losses))*100) +'%')
