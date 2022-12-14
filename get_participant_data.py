import json

def extract_player_data(json_obj, puuid):
  for participant in json_obj["info"]["participants"]:
    if participant["puuid"] == puuid:
      return participant

# Open the JSON file
with open("league_match.json") as file:
  # Load the JSON data from the file
  json_data = json.load(file)

# Use the data
#print(data)
# Extract the data for the player with puuid "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ"
player_data = extract_player_data(json_data, "hu7LrPvdnAMQSYttZlgmBKtyQ4EV2nW_24YFZP5xeQgayOhqcsj8oez8ksHprMRW1scJC7ENFyD-FQ")

# Print the extracted data for the player
print(player_data)
