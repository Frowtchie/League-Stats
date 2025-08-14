# League Stats

A Python application for analyzing personal League of Legends performance from match data via the Riot Games API. Get detailed insights into your gameplay, track improvement, and identify areas for growth.

## Features

- **Personal Match Data**: Fetch match history from Riot Games API with rate limiting and caching
- **Performance Analysis**: Deep dive into your KDA, win rates, and performance trends over time  
- **Champion Mastery**: Track your performance on different champions and identify your strongest picks
- **Role Analysis**: Compare your performance across different roles and positions
- **Objective Control**: Analyze your team's dragon, baron, and herald control
- **Economic Efficiency**: Track farming performance, gold efficiency, and damage per gold
- **Early Game Analysis**: Monitor first blood statistics and early game performance
- **Progression Tracking**: Visualize improvement trends and identify patterns
- **Multi-player Support**: Analyze multiple accounts with secure configuration
- **Robust Caching**: Avoid redundant API calls with intelligent match caching

## Prerequisites

- Python 3.8 or higher
- A valid API key from [Riot Developer Portal](https://developer.riotgames.com/)

## Installation

### Quick Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/Frowtchie/League-Stats.git
cd League-Stats

# Run the automated setup script
python setup.py
```

The setup script will:
- Check Python version compatibility
- Install all dependencies
- Create configuration files
- Set up necessary directories
- Run tests to verify installation

### Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/Frowtchie/League-Stats.git
cd League-Stats
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment:
```bash
# Copy the example config file
cp config.env.example config.env

# Edit config.env and add your API token:
export RIOT_API_TOKEN="your_api_token_here"

# Load the configuration
source config.env
```

## Usage

### Fetch Match Data

```bash
# Fetch last 10 matches for a player
python league.py Frowtch 10

# With debug logging
python league.py Frowtch 5 --log-level DEBUG
```

### Generate Personal Performance Visualizations

```bash
# Generate comprehensive performance analysis
python stats_visualization/visualizations/personal_performance.py Frowtch

# Generate specific chart types
python stats_visualization/visualizations/personal_performance.py Frowtch --chart trends
python stats_visualization/visualizations/personal_performance.py Frowtch --chart champions
python stats_visualization/visualizations/personal_performance.py Frowtch --chart roles

# Generate objective control analysis
python stats_visualization/visualizations/objective_analysis.py Frowtch

# Generate farming and economy analysis
python stats_visualization/visualizations/farming_analysis.py Frowtch

# Generate updated champion-specific charts
python stats_visualization/visualizations/graph_drakes.py Frowtch
python stats_visualization/visualizations/graph_barons_heralds.py Frowtch
python stats_visualization/visualizations/graph_kills.py Frowtch
python stats_visualization/visualizations/graph_first_bloods.py Frowtch
```

### Analyze Match Data

```bash
# Analyze player performance
python analyze.py --player Frowtch

# Team-wide analysis across all matches
python analyze.py --team-analysis

# Analyze matches from custom directory
python analyze.py --player Frowtch --matches-dir custom_matches/
```

## Configuration

### Environment Variables

- `RIOT_API_TOKEN` (required): Your Riot Games API token
- `PUUID_FROWTCH` (optional): PUUID for Frowtch player
- `PUUID_OVEROWSER` (optional): PUUID for Overowser player  
- `PUUID_SURO` (optional): PUUID for Suro player

### Adding New Players

To add a new player, set their PUUID as an environment variable:
```bash
export PUUID_NEWPLAYER="their_puuid_here"
```

### Finding Player PUUIDs

You can find PUUIDs using the Riot API account-v1 endpoint. Here's how:

#### Method 1: Using the Riot API directly

**Prerequisites:**
- Riot API key (get one from [Riot Developer Portal](https://developer.riotgames.com/))
- Player's game name and tag line (e.g., "Faker#T1")

**API Endpoint:**
```
GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}
```

**Example using curl:**
```bash
# Replace YOUR_API_KEY with your actual API key
# Replace Faker and T1 with the player's game name and tag line
curl -X GET "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Faker/T1" \
     -H "X-Riot-Token: YOUR_API_KEY"
```

**Example using Python:**
```python
import requests

api_key = "YOUR_API_KEY"
game_name = "Faker"
tag_line = "T1"

url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
headers = {"X-Riot-Token": api_key}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    puuid = data["puuid"]
    print(f"PUUID for {game_name}#{tag_line}: {puuid}")
else:
    print(f"Error: {response.status_code}")
```

**Response format:**
```json
{
  "puuid": "abc123def456...",
  "gameName": "Faker",
  "tagLine": "T1"
}
```

#### Method 2: Using online tools

You can also use online PUUID lookup tools, but make sure they're from trusted sources as they require your API key or player information.

**Important Notes:**
- Use the appropriate regional endpoint (`americas.api.riotgames.com`, `europe.api.riotgames.com`, or `asia.api.riotgames.com`)
- Rate limits apply (100 requests per 2 minutes for personal API keys)
- The PUUID is the `puuid` field in the response

## Project Structure

```
League-Stats/
├── league.py                    # Main data fetching script
├── analyze.py                   # Core analysis module
├── requirements.txt             # Python dependencies
├── config.env.example          # Configuration template
├── stats_visualization/         # Personal performance visualization modules
│   └── visualizations/
│       ├── personal_performance.py  # Comprehensive performance analysis
│       ├── objective_analysis.py    # Objective control analysis
│       ├── farming_analysis.py      # Economy and farming analysis
│       ├── graph_drakes.py          # Dragon control visualization
│       ├── graph_barons_heralds.py  # Baron/Herald visualization
│       ├── graph_kills.py           # Kill performance analysis
│       └── graph_first_bloods.py    # Early game analysis
├── tests/                      # Unit tests
├── matches/                    # Generated match data (gitignored)
└── docs/                       # Documentation

```

## Analysis Features

### Performance Tracking
- **KDA Trends**: Track kill/death/assist ratios over time with trend analysis
- **Win Rate Progression**: Monitor improvement in win rates across games  
- **Champion Mastery**: Identify your best champions with detailed performance metrics
- **Role Performance**: Compare effectiveness across different positions

### Objective Analysis
- **Dragon Control**: Analyze dragon priority and control rates
- **Baron/Herald**: Track major objective control and impact on win rate
- **First Objectives**: Monitor success rates for early objectives
- **Objective Correlation**: See how objective control affects game outcomes

### Economic Analysis  
- **CS per Minute**: Track farming efficiency and improvement trends
- **Gold Efficiency**: Analyze gold generation and spending effectiveness
- **Damage per Gold**: Monitor combat effectiveness relative to resources
- **Role-based Economy**: Compare economic performance across positions

### Early Game Analysis
- **First Blood Statistics**: Track early game aggression and success
- **Lane Phase Performance**: Monitor early game kill/death patterns
- **Early Objective Control**: Analyze first tower and early dragon control

## Development

### Running Tests

```bash
python -m unittest discover tests/ -v
```

### Adding New Analysis Features

1. Create a new file in `stats_visualization/visualizations/`
2. Implement data extraction and plotting functions
3. Follow the existing pattern of loading match data and extracting player-specific information
4. Add corresponding tests in the `tests/` directory

### Example: Creating a New Analysis Module

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
import league
import analyze

def extract_custom_data(player_puuid: str, matches_dir: str = "matches"):
    matches = analyze.load_match_files(matches_dir)
    # Extract and process your custom data
    return processed_data

def plot_custom_analysis(player_name: str, data):
    # Create your visualization
    pass

def main():
    # Standard argument parsing and execution
    pass

if __name__ == "__main__":
    main()
```

## API Rate Limits

The Riot Games API has rate limits. This application includes:
- Request timeout handling
- Proper error logging
- Retry logic for failed requests

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: Frowtch#0001 on Discord
