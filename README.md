# League Stats
This project provides a simple Python script for fetching data from the Riot Games API and saving it as JSON files.

## Prerequisites
- Python 3
- The `subprocess` and `json` modules
- A valid API key from Riot Games

## Usage
To use the script, modify the matches and token variables at the top of the script to specify the list of matches to fetch data for and your API key, respectively.

Then, run the script using the following command:
```
python fetch_api_data.py
```
This will fetch data for each match in the `matches` list and save it as a JSON file in a `matches` directory, using the match ID as the filename.

## Customization
You can customize the behavior of the script by modifying the code as needed. For example, you can change the URL of the API endpoint, add additional headers or parameters to the `curl` command, or adjust the formatting of the output JSON files. Refer to the inline comments in the code for more information.
