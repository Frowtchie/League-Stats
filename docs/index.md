# League Stats Documentation

Welcome to the documentation site for **League Stats** – a toolkit for collecting, analyzing and visualizing your personal League of Legends match history.

## Quick Start

1. Clone the repository
2. Install dependencies
3. Configure your Riot API token in `config.env`
4. Fetch matches with the CLI
5. Generate analytics and charts

See the sections in the left navigation for deeper details.

## Key Features

- Local match caching to minimize API calls
- Flexible filtering (queues, game modes, ARAM exclusion)
- Comprehensive visualization suite (objectives, economy, performance trends, jungle clears, etc.)
- Extensible architecture: each visualization is a focused module

## Project vs. Live Data

This site is static (built by MkDocs) and does **not** call the Riot API. All dynamic analysis still happens locally via the CLI (and forthcoming GUI). To publish example charts on the site you can:

1. Generate PNGs locally in the `output/` directory
2. Commit selected images under `docs/examples/` (create if needed)
3. Reference them in documentation pages with standard Markdown image syntax

## Adding Example Charts

Create a directory:

```
docs/examples/
```

Copy representative PNGs (avoid personally identifying info if sharing publicly) and embed:

```markdown
![Performance Trends](examples/performance_trends_DemoPlayer.png)
```

## Contributing

See the Contributing page for guidelines. For any user‑visible change remember to update docs and (if releasing) the changelog.

---
Generated with MkDocs Material.
