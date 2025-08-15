# League Stats

A Python application for analyzing personal League of Legends performance from match data via the Riot Games API. Get detailed insights into your gameplay, track improvement, and identify areas for growth.

## Version

Current version: **0.2.0**  
See the [Changelog](docs/changelog.md) for release notes.

## Features

- **Personal Match Data**: Fetch match history from Riot Games API with rate limiting and caching
- **Performance Analysis**: Deep dive into your KDA, win rates, and performance trends over time  
- **Champion Mastery**: Track your performance on different champions and identify your strongest picks
- **Role Analysis**: Compare your performance across different roles and positions
- **Objective Control**: Analyze your team's dragon, baron, and herald control
- **Economic Efficiency**: Track farming performance, gold efficiency, and damage per gold
- **Early Game Analysis**: Monitor first blood statistics and early game performance
- **Jungle Clear Analysis**: ⭐ **NEW!** Calculate first jungle clear times for jungle games with timeline data
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
RIOT_API_TOKEN=your_api_token_here
# (No need to source config.env; it is loaded automatically by the scripts)
```

## Usage
**Note:** All generated figures and analysis outputs are saved in the `output/` directory. Logs are written to the `logs/` directory.

### Fetch Match Data

```bash
# Fetch last 10 matches for a player by their Riot ID (game name + tag)
python league.py frowtch blue 10

# Examples with different players
python league.py Faker T1 5
python league.py Hide on bush KR1 15

# With debug logging and no cache
python league.py frowtch blue 5 --log-level DEBUG --no-cache
```

**Note**: The script now uses Riot ID (game name + tag line) instead of predefined player names. This allows fetching data for any player without needing to configure PUUIDs in advance.

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

# Generate jungle clear time analysis (NEW!)
python stats_visualization/visualizations/jungle_clear_analysis.py Frowtch

# Generate updated champion-specific charts
python stats_visualization/visualizations/graph_drakes.py Frowtch
python stats_visualization/visualizations/graph_barons_heralds.py Frowtch
python stats_visualization/visualizations/graph_kills.py Frowtch
python stats_visualization/visualizations/graph_first_bloods.py Frowtch
```


### Analyze Match Data

```bash
# Analyze player performance (recommended, by Riot ID)
python analyze.py --riot-id Frowtch blue

# Analyze player performance (legacy mode, by config name)
python analyze.py --player Frowtch

# Team-wide analysis across all matches
python analyze.py --team-analysis

# Analyze matches from custom directory
python analyze.py --riot-id Frowtch blue --matches-dir custom_matches/
```

## Configuration

### Environment Variables

- `RIOT_API_TOKEN` (required): Your Riot Games API token

**Note**: With the new Riot ID-based player lookup, you no longer need to configure individual player PUUIDs. The script will automatically fetch PUUIDs using the Riot API when you provide a game name and tag line.

**No need to source config.env manually:** All scripts automatically load environment variables from `config.env`.

### Regional Endpoints

The script uses the Americas endpoint (`americas.api.riotgames.com`) for account data by default, which covers:
- North America (NA)
- Brazil (BR) 
- Latin America North (LAN)
- Latin America South (LAS)
- Oceania (OCE)

For players in other regions, the script will still work as account data is accessible across regional boundaries.

### Getting Your Riot API Token

1. Go to the [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your Riot account
3. Create a new application or use an existing one
4. Copy your API key
5. Add it to your config.env file:

```
RIOT_API_TOKEN=your_api_key_here
```

### Finding Player Information

To use this tool, you only need a player's **Riot ID**, which consists of:
- **Game Name**: The display name (e.g., "Faker", "Hide on bush")  
- **Tag Line**: The identifier after the # symbol (e.g., "T1", "KR1")

You can find this information:
1. **In-game**: Look at the player's profile or match history
2. **League client**: Check recent games or friend lists
3. **Third-party sites**: Use sites like OP.GG, U.GG, or similar (search for the player and note their Riot ID)
4. **Ask the player**: The Riot ID is their current display name + tag

**Examples of valid Riot IDs:**
- `Faker#T1`
- `Hide on bush#KR1` 
- `Doublelift#NA1`
- `frowtch#blue`

The script will automatically fetch the player's PUUID using their Riot ID, so you don't need to manually look up PUUIDs anymore.

### Legacy PUUID Configuration (Optional)

The old PUUID-based configuration is still supported for backwards compatibility, but it's no longer recommended. If you have environment variables like `PUUID_FROWTCH` set, the `load_player_config()` function will still work, but the main script now uses the new Riot ID approach.

## Project Structure

```
League-Stats/
├── league.py                    # Main data fetching script
├── analyze.py                   # Core analysis module
├── requirements.txt             # Python dependencies
├── config.env.example           # Configuration template
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
├── output/                     # All generated figures and analysis outputs
├── logs/                       # Log files
└── docs/                       # Documentation (see docs/README or index below)
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

## Documentation Index

Extended documentation lives in the `docs/` folder:
- Overview: `docs/overview.md`
- Architecture: `docs/architecture.md`
- CLI Reference: `docs/cli_reference.md`
- Metrics Definitions: `docs/metrics_definitions.md`
- Visualizations Catalog: `docs/visualizations_catalog.md`
- Fetching Logic: `docs/fetching_logic.md`
- Player Configuration: `docs/player_config.md`
- Environment Setup: `docs/environment.md`
- Contributing Guide: `docs/contributing.md`
- Troubleshooting: `docs/troubleshooting.md`
- Changelog: `docs/changelog.md`

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
