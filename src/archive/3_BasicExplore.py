# ===========================================================
# Chess.com Blitz Game Analysis (Unified + Cleaned)
# ===========================================================
# This script:
#   - Loads your merged chess.com CSV
#   - Parses datetime
#   - Identifies your colour and ratings
#   - Computes rating difference
#   - Extracts move counts
#   - Analyses game length vs outcomes
#   - Analyses performance vs rating difference
#   - Shows rolling performance trends
# ===========================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

%matplotlib inline

# ------------------------
# 1. Load the dataset
# ------------------------
df = pd.read_csv("../data/all_games_merged.csv")

# ------------------------
# 2. Create datetime column
# ------------------------
df["datetime"] = pd.to_datetime(
    df["date"] + " " + df["time"],
    format="%Y.%m.%d %H:%M:%S",
    errors="coerce"
)

df = df.sort_values("datetime").reset_index(drop=True)
df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month

# ------------------------
# 3. Identify your colour
# ------------------------
your_name = "RhysLWells"

df["color"] = df.apply(
    lambda r: "white" if r["white"] == your_name else "black",
    axis=1
)

# ------------------------
# 4. Extract your Elo and opponent Elo
# ------------------------
df["your_elo"] = df.apply(
    lambda r: r["white_elo"] if r["color"] == "white" else r["black_elo"],
    axis=1
)

df["opponent_elo"] = df.apply(
    lambda r: r["black_elo"] if r["color"] == "white" else r["white_elo"],
    axis=1
)

# Rating difference (positive = opponent stronger)
df["rating_diff"] = df["opponent_elo"] - df["your_elo"]

# ------------------------
# 5. Convert game results to numerical score
# ------------------------
def result_score(row):
    if row["color"] == "white":
        if row["result"] == "1-0": return 1
        if row["result"] == "0-1": return 0
        return 0.5
    else:
        if row["result"] == "0-1": return 1
        if row["result"] == "1-0": return 0
        return 0.5

df["score"] = df.apply(result_score, axis=1)

# ===========================================================
# 6. Extract number of moves + length statistics
# ===========================================================
df["move_count"] = df["moves_san"].apply(
    lambda x: len(str(x).split()) if pd.notnull(x) else 0
)

print("Average game length:", df["move_count"].mean())
print("Median game length:", df["move_count"].median())
print("Shortest game:", df["move_count"].min())
print("Longest game:", df["move_count"].max())

# Histogram
plt.figure(figsize=(8,4))
plt.hist(df["move_count"], bins=20)
plt.title("Distribution of Game Length (Moves)")
plt.xlabel("Move Count")
plt.ylabel("Count")
plt.show()

# Correlation with outcome
correlation = df["move_count"].corr(df["score"])
print("Correlation between game length and score:", correlation)

plt.figure(figsize=(8,4))
plt.scatter(df["move_count"], df["score"])
plt.title("Outcome vs Move Count")
plt.xlabel("Move Count")
plt.ylabel("Score")
plt.show()

# Category for boxplot
df["result_category"] = df["score"].apply(
    lambda s: "win" if s == 1 else ("loss" if s == 0 else "draw")
)

df.boxplot(column="move_count", by="result_category", figsize=(8,5))
plt.title("Game Length by Result Category")
plt.suptitle("")
plt.xlabel("Result")
plt.ylabel("Move Count")
plt.show()

# ===========================================================
# 7. Rating difference & performance analysis
# ===========================================================
# Positive => opponent stronger
df["out_rated"] = df["rating_diff"] > 0

print("Performance vs stronger opponents:", df[df["out_rated"]]["score"].mean())
print("Performance vs weaker opponents:", df[~df["out_rated"]]["score"].mean())

plt.figure(figsize=(8,4))
plt.scatter(df["rating_diff"], df["score"])
plt.axvline(0, linestyle="dashed")
plt.title("Performance by Rating Difference")
plt.xlabel("Opponent_Elo - Your_Elo")
plt.ylabel("Score")
plt.show()

# Group bins for deeper rating-diff analysis
df["rating_bin"] = pd.cut(
    df["rating_diff"],
    bins=[-500, -100, 0, 100, 300, 500],
    labels=["Much stronger", "Stronger", "Equal", "Opponent +100", "Opponent +300"]
)

rating_bin_stats = df.groupby("rating_bin")["score"].mean()
print("Score by rating gap:")
print(rating_bin_stats)

rating_bin_stats.plot(kind="bar", figsize=(8,4))
plt.title("Score by Rating Difference Band")
plt.ylabel("Score")
plt.show()

# ===========================================================
# 8. Rolling win-rate when outrated vs higher rated (fixed)
# ===========================================================

# Ensure index represents game order
df = df.reset_index(drop=True)

# Build score series
df["score_vs_higher"] = df.apply(
    lambda r: r["score"] if r["rating_diff"] > 0 else np.nan, axis=1
).astype(float)

df["score_vs_lower"] = df.apply(
    lambda r: r["score"] if r["rating_diff"] < 0 else np.nan, axis=1
).astype(float)

# Rolling averages with minimum periods to allow early games to count
rolling_higher = df["score_vs_higher"].rolling(window=20, min_periods=1).mean()
rolling_lower  = df["score_vs_lower"].rolling(window=20, min_periods=1).mean()

plt.figure(figsize=(12,5))

# Plot only valid points
plt.plot(df.index, rolling_higher, label="When Opponent Higher Rated")
plt.plot(df.index, rolling_lower,  label="When You Are Higher Rated")

plt.xlabel("Game Number")
plt.ylabel("Rolling Win Rate (20 games)")
plt.title("Rolling Win Rate vs Relative Rating")
plt.legend()
plt.grid(True)
plt.show()


# ===========================================================
# 9. Summary
# ===========================================================
print("Total games:", len(df))
print("Overall performance (score):", df["score"].mean())
print("Average move count:", df["move_count"].mean())
print("Average rating difference:", df["rating_diff"].mean())

# ===========================================================
# 10. Your Elo progression over time
# ===========================================================

# Ensure games are sorted by time
df = df.sort_values("datetime").reset_index(drop=True)

# Extract your ELO (already computed earlier as df["your_elo"])
elo_series = df["your_elo"]
game_numbers = df.index

plt.figure(figsize=(12,5))
plt.plot(game_numbers, elo_series, linewidth=2)

plt.xlabel("Game Number (Chronological)")
plt.ylabel("Your Elo")
plt.title("Elo Progression Over Time")
plt.grid(True)
plt.show()

print("Starting Elo:", elo_series.iloc[0])
print("Latest Elo:", elo_series.iloc[-1])
print("Elo Change:", elo_series.iloc[-1] - elo_series.iloc[0])

# ===========================================================
# (Optional) Elo progression by color
# ===========================================================

df["game_num"] = df.index  # ensure clean x-axis

plt.figure(figsize=(12,5))

plt.plot(df[df["color"]=="white"]["game_num"],
         df[df["color"]=="white"]["your_elo"],
         label="White Elo Progression",
         linewidth=2)

plt.plot(df[df["color"]=="black"]["game_num"],
         df[df["color"]=="black"]["your_elo"],
         label="Black Elo Progression",
         linewidth=2)

plt.xlabel("Game Number")
plt.ylabel("Your Elo")
plt.title("Elo Progression Over Time (White vs Black)")
plt.legend()
plt.grid(True)
plt.show()

# --------------------------------------------
# Elo Volatility Calculation
# --------------------------------------------

# Compute game-to-game rating changes
df = df.sort_values("date")
df["rating_change"] = df["rating"].diff()

# Volatility (standard deviation of rating change)
elo_volatility = df["rating_change"].std()

print(f"Elo volatility: {elo_volatility:.2f}")

# --------------------------------------------
# Smoothed Elo Curve Using Rolling Mean
# --------------------------------------------

# Use a 20-game rolling window; adjust as needed
df["elo_smooth"] = df["rating"].rolling(window=20, center=True).mean()
# --------------------------------------------
# Identify Local Peaks and Troughs in Rating
# --------------------------------------------

df["peak"] = (df["rating"] > df["rating"].shift(1)) & (df["rating"] > df["rating"].shift(-1))
df["trough"] = (df["rating"] < df["rating"].shift(1)) & (df["rating"] < df["rating"].shift(-1))

peaks = df[df["peak"]]
troughs = df[df["trough"]]

print(f"Number of peaks: {len(peaks)}")
print(f"Number of troughs: {len(troughs)}")

# --------------------------------------------
# Plot Elo Progression with Smoothed Curve
# --------------------------------------------

import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(df["date"], df["rating"], label="Elo", alpha=0.7)
plt.plot(df["date"], df["elo_smooth"], label="Smoothed Elo", linewidth=2)

# Highlight peaks and troughs
plt.scatter(peaks["date"], peaks["rating"], label="Peaks")
plt.scatter(troughs["date"], troughs["rating"], label="Troughs")

plt.xlabel("Date")
plt.ylabel("Rating")
plt.title("Elo Progression Over Time")
plt.legend()
plt.tight_layout()
plt.show()
