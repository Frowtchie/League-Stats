# League Stats

A Python application for fetching League of Legends match data from the Riot Games API and creating visualizations.

## Features

- **Data Fetching**: Fetch match data from Riot Games API with rate limiting and caching
- **Data Storage**: Store match data as JSON files with validation
- **Data Analysis**: Analyze player performance and team statistics
- **Visualizations**: Create charts for game statistics (drakes, barons, heralds, kills)
- **Multi-player Support**: Support for multiple players with secure configuration
- **Robust Error Handling**: Proper logging, retries, and validation
- **Caching System**: Avoid redundant API calls with intelligent caching

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

### Generate Visualizations

```bash
# Generate drake statistics
python stats_visualization/visualizations/graph_drakes.py

# Generate baron and herald statistics  
python stats_visualization/visualizations/graph_barons_heralds.py LEC

# Generate kill statistics
python stats_visualization/visualizations/graph_kills.py TeamName LEC
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

You can find PUUIDs using the Riot API account-v1 endpoint.

## Project Structure

```
League-Stats/
├── league.py                    # Main data fetching script
├── requirements.txt             # Python dependencies
├── config.env.example          # Configuration template
├── stats_visualization/         # Visualization modules
│   └── visualizations/
│       ├── graph_drakes.py     # Drake statistics
│       ├── graph_barons_heralds.py  # Baron/Herald stats
│       ├── graph_kills.py      # Kill statistics
│       └── graph_first_bloods.py    # First blood stats
├── tests/                      # Unit tests
├── matches/                    # Generated match data (gitignored)
└── docs/                       # Documentation

```

## Development

### Running Tests

```bash
python -m unittest discover tests/ -v
```

### Adding New Visualizations

1. Create a new file in `stats_visualization/visualizations/`
2. Implement data reading and plotting functions
3. Add corresponding tests in the `tests/` directory

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
