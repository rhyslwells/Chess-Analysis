# Building a Chess Analysis App - Exploring the Chess.com API with Python

*How I interacted with the Chess.com API for the chess analysis application*

## Introduction

As part of my Streamlit [Chess Analysis](https://chess-analysis.streamlit.app/) project, one of the first challenges was fetching and processing game data from Chess.com. While Chess.com provides [Published Data API](https://www.chess.com/news/view/published-data-api), working with it directly presents several challenges: navigating monthly archive pagination, handling edge cases in game timing data, and structuring JSON responses for analysis.

This post explores how I built the `ChessDataFetcher` class to handle these challenges. I'll use real data from my account as a working example, to demonstrate the system in action.

## The Chess.com API: Structure and Challenges

Chess.com organises game data into monthly archives. The `ChessDataFetcher` class encapsulates this pipeline:

```
Chess.com API -> Fetch Games -> Validate Data -> Process -> DataFrame
```

## Architecture: From API to Analysis

The fetcher provides three key capabilities:

### 1. Archive Discovery

The first step is discovering what data exists:

```python
from src.data_fetcher import ChessDataFetcher

fetcher = ChessDataFetcher()
archives = fetcher.get_available_archives("RhysLWells")
```

This queries `https://api.chess.com/pub/player/{username}/games/archives` and returns monthly archive URLs:

| Month | Archive URL |
|-------|-------------|
| 2025-09 | https://api.chess.com/pub/player/rhyslwells/games/2025/09 |
| 2025-10 | https://api.chess.com/pub/player/rhyslwells/games/2025/10 |
| 2025-11 | https://api.chess.com/pub/player/rhyslwells/games/2025/11 |
| 2025-12 | https://api.chess.com/pub/player/rhyslwells/games/2025/12 |
| 2026-01 | https://api.chess.com/pub/player/rhyslwells/games/2026/01 |

### 2. Bulk Fetching

Rather than manually requesting each archive, `fetch_all_games()` automates the process:

```python
all_games = fetcher.fetch_all_games("RhysLWells", limit_months=12)
```

This method:
- Calls `get_available_archives()` and iterates through each monthly archive  
- Implements rate limiting (0.5s delay between requests)
- Returns a complete list of game dictionaries

Running this on my account: 264 games fetched across 123 days (2025-09-15 to 2026-01-16). The [API](https://rhyslwells.github.io/Data-Archive/categories/devops/API) provides metadata for each game stored in JSON, including time control classification (blitz, bullet, rapid), player ratings, results, and [PGN](https://rhyslwells.github.io/Data-Archive/categories/OTHER/PGN) data.

### 3. Data Validation

Raw API data isn't always clean. During development, I discovered games with negative durations (derived from PGNs). This would corrupt any time-based analysis. I found three main edge cases causing this:

- Midnight Crossings:Game starts at 23:50:00, ends at 00:10:00
- Timezone Issues: Durations > 24 hours
- Missing Data: No start time in PGN headers

The `validate_game_durations()` method addresses these issues.


## Processing: From JSON to DataFrame

The final step is transforming raw data into a structured format suitable for analysis. The `process_and_save()` method transforms (validated) raw API responses into structured pandas DataFrames:

```python
df = fetcher.process_and_save("RhysLWells", all_games, mode='json')
```

The `process_and_save()` method performs the following steps:

**Processing steps:**
1. Parse each game's metadata (ratings, results, openings, ECO codes)
2. Calculate results from user's perspective (win/loss/draw)
3. Validate game durations using the logic above
4. Remove duplicates (based on timestamp + opponent)

And builds a DataFrame with the following columns:

**Extracted columns:**

| Category | Fields |
|----------|--------|
| Temporal | date, timestamp |
| Players | user_color, opponent, user_rating, opponent_rating |
| Results | result, result_label |
| Opening | opening, eco, eco_url |
| Metadata | time_control, game_url, game_duration_seconds, pgn |

**Performance**: Processing 264 games takes approximately less that 15 seconds, primarily limited by API rate constraints.


## Initial Insights

With clean, validated data, we can extract interesting patterns:

### Opening Repertoire

From the opening data, we see the most frequently played openings:

| Opening | Games | % |
|---------|-------|---|
| Nimzowitsch Defense 2.D4 E6 3.Nf3 D5 4.E5 | 15 | 5.7% |
| French Defense Knight Variation | 10 | 3.8% |
| Philidor Defense 3.Bc4 | 8 | 3.0% |
| French Defense Advance Variation | 8 | 3.0% |
| Italian Game | 8 | 3.0% |

For myself, French Defense appears frequently across multiple variations, so it's a key part of my repertoire.

### Performance by Color

From the results data, we can summarise performance by color:

| Color | Win Rate | W | L | D | Total |
|-------|----------|---|---|---|-------|
| White | 45.1% | 56 | 69 | 7 | 132 |
| Black | 49.6% | 63 | 64 | 5 | 132 |

## Design Principles

Two key decisions I made to ensure reliability where:

**API Etiquette**: We identify the application via User-Agent headers
```python
HEADERS = {"User-Agent": "Chess Analysis Dashboard (Python/requests)"}
```
This helps Chess.com track API usage and contact developers if issues arise.

**Rate Limiting**: A 0.5-second delay between requests prevents overwhelming the API
```python
time.sleep(0.5)  # Respect API constraints
```
This avoids potential IP bans while maintaining reasonable fetch times (264 games in ~15 seconds).


## Conclusion

The `ChessDataFetcher` class solves the complexity of working with the Chess.com API by handling archive discovery, rate limiting, data validation, and structuring automatically. With this data in hand I can proceed to further analysis and prediction in the chess analysis dashboard.