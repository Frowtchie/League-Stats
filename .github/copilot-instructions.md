# League Stats - GitHub Copilot Instructions

League Stats is a Python application for analyzing personal League of Legends performance from match data via the Riot Games API. This tool fetches match data, performs statistical analysis, and generates visualizations to help players track improvement and identify areas for growth.

**ALWAYS follow these instructions first. Only search for additional information or run exploratory bash commands if the information here is incomplete or incorrect.**

## Working Effectively

### Bootstrap and Setup
- **CRITICAL**: Python 3.8+ is required. Verify with `python3 --version`
- Run the automated setup (takes ~30 seconds): `python3 setup.py`
  - This installs all dependencies, creates directories, and runs tests
  - **NEVER CANCEL** - setup completes in 30 seconds, set timeout to 60+ seconds
- Alternative manual setup:
  ```bash
  pip install -r requirements.txt
  cp config.env.example config.env
  # Edit config.env and add your RIOT_API_TOKEN
  ```

### Configuration Requirements
- **REQUIRED**: Get Riot API token from https://developer.riotgames.com/
- Edit `config.env` and uncomment/set: `export RIOT_API_TOKEN="your_token_here"`
- Load configuration: `source config.env`
- **WARNING**: Commands fail with "RIOT_API_TOKEN environment variable is not set" if token not configured

### Testing
- Run full test suite: `python3 -m unittest discover tests/ -v`
- Tests complete in <1 second, **NEVER CANCEL** - set timeout to 30+ seconds  
- 19 tests cover main functionality (league.py, analyze.py, visualizations)
- All tests should pass on a fresh setup

### Code Quality and Linting
- **ALWAYS run before committing**:
  ```bash
  black --check .          # Format checking (~1-2 seconds)
  flake8 .                 # Linting (~1 second)  
  mypy .                   # Type checking (~10 seconds, shows known type issues)
  ```
- Fix formatting: `black .`
- **NEVER CANCEL** linting operations - complete in seconds (mypy takes ~10 seconds)

## Core Functionality

### Data Fetching
- Fetch match data: `python3 league.py <game_name> <tag_line> <count>`
- Example: `python3 league.py Frowtch blue 5`
- Saves JSON files to `matches/` directory
- **Requires valid RIOT_API_TOKEN in environment**

### Data Analysis  
- Analyze player data: `python3 analyze.py --player <player_name>`
- Team analysis: `python3 analyze.py --team-analysis`
- **NOTE**: Returns "No match data found" if no matches in `matches/` directory

### Visualizations
Generate performance charts with scripts in `stats_visualization/visualizations/`:
```bash
# Comprehensive analysis (uses Riot ID format: game_name + tag_line)
python3 stats_visualization/visualizations/personal_performance.py <game_name> <tag_line>

# Specific chart types  
python3 stats_visualization/visualizations/personal_performance.py <game_name> <tag_line> --chart trends
python3 stats_visualization/visualizations/personal_performance.py <game_name> <tag_line> --chart champions
python3 stats_visualization/visualizations/personal_performance.py <game_name> <tag_line> --chart roles

# Specialized analysis (uses legacy player name format)
python3 stats_visualization/visualizations/objective_analysis.py <player_name>
python3 stats_visualization/visualizations/farming_analysis.py <player_name>
python3 stats_visualization/visualizations/graph_drakes.py <player_name>
python3 stats_visualization/visualizations/graph_barons_heralds.py <player_name>
python3 stats_visualization/visualizations/graph_kills.py <player_name>
python3 stats_visualization/visualizations/graph_first_bloods.py <player_name>
```

**NOTE**: Different scripts use different argument formats:
- `personal_performance.py` requires both `game_name` and `tag_line` (e.g., `Frowtch blue`)
- Other visualization scripts use single `player_name` argument (e.g., `Frowtch`)

## Validation Scenarios

**ALWAYS test these scenarios after making changes:**

### 1. Setup Validation
```bash
# Fresh setup
python3 setup.py
# Should complete successfully with "🎉 SETUP COMPLETE!" message
```

### 2. Configuration Validation  
```bash
# Test without API token
python3 league.py testplayer tag 1
# Should fail with: "RIOT_API_TOKEN environment variable is not set"

# Test with configuration
source config.env
echo $RIOT_API_TOKEN
# Should show your token value
```

### 3. Analysis Validation
```bash
# Test with no data
python3 analyze.py --player TestPlayer  
# Should show: "No match data found. Run league.py first to fetch some matches."
```

### 4. Test Suite Validation
```bash
python3 -m unittest discover tests/ -v
# All 19 tests should pass in <1 second
```

### 5. Visualization Validation
```bash
# Test personal performance (expects RIOT_API_TOKEN and tries to fetch data)
python3 stats_visualization/visualizations/personal_performance.py Frowtch blue --chart trends
# Should either fetch data from API or show "No matches found"

# Test other visualizations (handles missing data gracefully)
python3 stats_visualization/visualizations/graph_drakes.py Frowtch
# Should show: "No matches found for Frowtch" and exit cleanly
```

### 6. Code Quality Validation
```bash
# Check formatting and linting
black --check .
flake8 .
# Fix any issues before committing
```

## Project Structure

### Key Files and Directories
```
.
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies  
├── setup.py                 # Automated setup script
├── config.env.example      # Configuration template
├── config.env              # Your configuration (created by setup)
├── league.py               # Data fetching from Riot API
├── analyze.py              # Data analysis and statistics  
├── stats_visualization/    # Visualization modules
│   └── visualizations/     # Individual chart generators
├── tests/                  # Unit tests
├── matches/               # JSON match data storage (created by setup)
└── logs/                  # Application logs (created by setup)
```

### Important Modules
- **league.py**: Fetches match data from Riot Games API, handles rate limiting
- **analyze.py**: Processes match data, calculates statistics, player performance metrics
- **stats_visualization/**: Matplotlib-based visualization generators
- **tests/**: Comprehensive test coverage for main functionality

## Timing Expectations

- **Setup**: 2-30 seconds depending on dependencies (**NEVER CANCEL** - set timeout to 60+ seconds)
- **Tests**: <1 second (**NEVER CANCEL** - set timeout to 30+ seconds)
- **Black formatting**: 1-2 seconds (**NEVER CANCEL**)
- **Flake8 linting**: ~1 second (**NEVER CANCEL**)
- **MyPy type checking**: ~10 seconds (**NEVER CANCEL**)
- **Data fetching**: Varies by API response time and match count
- **Visualization generation**: Seconds to minutes depending on data volume

## Common Issues and Solutions

### "RIOT_API_TOKEN environment variable is not set"
- Solution: Edit `config.env`, uncomment and set your API token, run `source config.env`

### "No match data found"  
- Solution: Run `python3 league.py <game_name> <tag_line> <count>` first to fetch data

### Import errors in tests
- Solution: Ensure you're in the repository root directory when running tests

### Formatting/linting failures
- Solution: Run `black .` to auto-format, fix remaining flake8 issues manually

### Matplotlib backend issues (in headless environments)
- The application uses 'agg' backend automatically for headless operation
- Visualizations generate successfully but cannot display interactively

## Development Workflow

1. **Always run setup first**: `python3 setup.py`
2. **Configure API token**: Edit `config.env`, run `source config.env`  
3. **Test your changes**: `python3 -m unittest discover tests/ -v`
4. **Fetch sample data** (if testing data-dependent features): `python3 league.py Frowtch blue 5`
5. **Validate visualizations**: Run relevant scripts in `stats_visualization/visualizations/`
6. **Run code quality checks**: `black --check .` and `flake8 .`
7. **Fix formatting**: `black .` if needed
8. **Final test**: Complete test suite should pass

### Release & Documentation Policy
Single source of truth for releases:
1. For any user‑visible change (CLI flags, outputs, file names, new/changed visualizations, data model fields, config behavior) update all impacted docs (README, changelog, visualization catalog, CLI reference, contributing).
2. If version bump needed: update `stats_visualization/__init__.__version__`, move Unreleased changelog entries under dated version, commit `chore(release): vX.Y.Z`, create and push annotated tag, optionally draft GitHub Release.
3. Use `RELEASE_CHECKLIST.md` for a quick pre‑tag audit.

Assistant Behavior: After qualifying changes the assistant will prompt: "User-visible changes detected; create a new release? (y/n)".

## API Rate Limits and Best Practices

- Riot API has rate limits - the application handles this automatically
- Use small match counts for testing (e.g., 5 matches)
- Match data is cached in `matches/` directory to avoid re-fetching
- Use `--no-cache` flag with league.py to force re-fetch if needed

**Remember: ALWAYS follow these instructions and validate your changes with the complete workflow before committing.**