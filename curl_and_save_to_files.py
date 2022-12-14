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

matches = ["EUW1_6185572887", "EUW1_6185488598", "EUW1_6185388008", "EUW1_6185318040", "EUW1_6185251325", "EUW1_6183970493", "EUW1_6183933821", "EUW1_6183897789", "EUW1_6183843307", "EUW1_6183811502", "EUW1_6183767642", "EUW1_6183704222", "EUW1_6183305709", "EUW1_6183269048", "EUW1_6183241901", "EUW1_6183206563", "EUW1_6182041959", "EUW1_6181991347", "EUW1_6181938977", "EUW1_6179302861"]
token ="RGAPI-25d4a16f-2c8b-443f-bd24-ff638cda1451"

for match in matches:
    # Set the headers for the curl command
    headers = ["-H", "Accept-Charset: application/x-www-form-urlencoded", "-H", "Origin: https://developer.riotgames.com", "-H", "X-Riot-Token: "+token]

    # Build the URL for the curl command
    url = "https://europe.api.riotgames.com/lol/match/v5/matches/" + match

    # Run the curl command and save the output
    output = subprocess.run(["curl", url, *headers], stdout=subprocess.PIPE)

    # Decode the output as a string
    json_string = output.stdout.decode("utf-8")

    # Load the JSON string as a Python object
    json_obj = json.loads(json_string)

    # Save the JSON object to a file
    with open(f"matches/{match}.json", "w") as f:
        json.dump(json_obj, f, indent=4)
