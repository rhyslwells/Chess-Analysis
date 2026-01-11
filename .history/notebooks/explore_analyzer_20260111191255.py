"""
explore_analyzer.py
Focused exploration of ChessAnalyzer features using real data.

This script generates a restricted set of analytical plots for the user
rhyslwells. It is intended for batch execution or interactive use.

Generated outputs are written to ./images/
"""

"""
## Benefits

why use analyzer
1. **Deeper Insights**: More granular understanding of performance patterns
2. **Trend Identification**: Spot improvement or decline earlier
3. **Strategy Optimization**: Understand what conditions favor your play
4. **Data-Driven Decisions**: Make informed choices about opening preparation, time controls, etc.
5. **Motivational Tracking**: Visualize progress and recovery from slumps
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.data_fetcher import ChessDataFetcher
from src.analyzer import ChessAnalyzer


# -----------------------------------------------------------
# Configuration
# -----------------------------------------------------------

USERNAME = "rhyslwells"
FETCH_NEW_DATA = False

BASE_DIR = Path(__file__).parent
IMAGE_DIR = BASE_DIR / "images"
IMAGE_DIR.mkdir(exist_ok=True)

plt.style.use("seaborn-v0_8-darkgrid")


# -----------------------------------------------------------
# Load data
# -----------------------------------------------------------

print("Loading data")

fetcher = ChessDataFetcher()

if FETCH_NEW_DATA:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    games = fetcher.fetch_multiple_months(USERNAME, start_date, end_date)
    df = fetcher.process_and_save(USERNAME, games, mode="json")
else:
    df = fetcher.load_existing_data(USERNAME)
    if df is None:
        raise RuntimeError("No existing data found. Set FETCH_NEW_DATA = True.")

print(f"Loaded {len(df)} games")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")


# -----------------------------------------------------------
# Initialize analyzer
# -----------------------------------------------------------

analyzer = ChessAnalyzer(df)


# -----------------------------------------------------------
# Fine-grained rating performance (20 bins)
# -----------------------------------------------------------

print("Generating fine-grained rating performance")

fine_perf = analyzer.get_fine_grained_rating_performance()

# Collapse into 20 bins at the visualization level
fine_perf["bin_group"] = pd.qcut(
    fine_perf.index, q=20, labels=False #TODO: issue want bins to be size 5.
)

agg_perf = (
    fine_perf
    .groupby("bin_group", as_index=False)
    .agg(
        rating_bin=("rating_bin", "first"),
        win_rate=("win_rate", "mean")
    )
)

plt.figure(figsize=(12, 6))
plt.bar(range(len(agg_perf)), agg_perf["win_rate"])
plt.xticks(range(len(agg_perf)), agg_perf["rating_bin"], rotation=30)
plt.axhline(y=50, linestyle="--", linewidth=1)
plt.xlabel("Rating difference bin")
plt.ylabel("Win rate (%)")
plt.title("Win Rate by Rating Difference (5 bins)")
plt.tight_layout()
plt.savefig(IMAGE_DIR / "fine_grained_rating_performance.png", dpi=300)
plt.close()


# -----------------------------------------------------------
# Opening repertoire
# -----------------------------------------------------------

print("Generating opening repertoire")

opening_stats = analyzer.get_opening_stats(top_n=10)

plt.figure(figsize=(12, 6))
plt.barh(
    range(len(opening_stats)),
    opening_stats["games"]
)
plt.yticks(range(len(opening_stats)), opening_stats["opening"])
plt.xlabel("Games played")
plt.title("Top 10 Openings")
plt.tight_layout()
plt.savefig(IMAGE_DIR / "opening_repertoire.png", dpi=300)
plt.close()


# -----------------------------------------------------------
# Rating progression
# -----------------------------------------------------------

print("Generating rating progression")

rating_trend = analyzer.get_rating_trend()
rating_smoothed = analyzer.get_rating_trend_with_smoothing(window=20)

plt.figure(figsize=(14, 6))
plt.plot(
    rating_trend["date"],
    rating_trend["user_rating"],
    alpha=0.4,
    label="Raw rating"
)
plt.plot(
    rating_smoothed["date"],
    rating_smoothed["elo_smooth"],
    linewidth=2,
    label="Smoothed (20-game mean)"
)
plt.xlabel("Date")
plt.ylabel("Rating")
plt.title("Rating Progression Over Time")
plt.legend()
plt.tight_layout()
plt.savefig(IMAGE_DIR / "rating_progression.png", dpi=300)
plt.close()


# -----------------------------------------------------------
# Rolling performance by opponent type
# -----------------------------------------------------------

print("Generating rolling performance by opponent type")

rolling_split = analyzer.get_rolling_performance_by_rating(window=20)

plt.figure(figsize=(14, 6))
plt.plot(
    rolling_split["date"],
    rolling_split["vs_higher_rated"] * 100,
    label="Vs higher rated",
    linewidth=2
)
plt.plot(
    rolling_split["date"],
    rolling_split["vs_lower_rated"] * 100,
    label="Vs lower rated",
    linewidth=2
)
plt.axhline(y=50, linestyle="--", linewidth=1)
plt.xlabel("Date")
plt.ylabel("Rolling win rate (%)")
plt.title("Rolling Win Rate by Opponent Type (20-game window)")
plt.legend()
plt.tight_layout()
plt.savefig(IMAGE_DIR / "rolling_by_opponent_type.png", dpi=300)
plt.close()


# -----------------------------------------------------------
# Summary
# -----------------------------------------------------------

print("Analysis complete")
print("Generated files:")
print(f" - {IMAGE_DIR / 'fine_grained_rating_performance.png'}")
print(f" - {IMAGE_DIR / 'opening_repertoire.png'}")
print(f" - {IMAGE_DIR / 'rating_progression.png'}")
print(f" - {IMAGE_DIR / 'rolling_by_opponent_type.png'}")
