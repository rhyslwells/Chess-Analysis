# ===========================================================
# Chess.com Blitz Game Analysis (Unified + Cleaned with Explanations)
# ===========================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

%matplotlib inline

print("Loading dataset... & Preprocessing...")
# ------------------------
# 1. Load the dataset
# ------------------------
"""
Load your merged CSV from Chess.com.
Takeaway: This is your raw game data, which includes date, time, players, ratings, results, openings, and moves.
"""
df = pd.read_csv("../data/all_games_merged.csv")

# ------------------------
# 2. Create datetime column
# ------------------------
"""
Combine date + time into a single datetime object.
Sorting by datetime allows chronological analysis.
Takeaway: Enables time-series analysis such as Elo progression or rolling performance.
"""
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
"""
Determine if you played as white or black in each game.
Takeaway: Knowing your color is necessary for correctly assigning Elo and computing score.
"""
your_name = "RhysLWells"
df["color"] = df.apply(lambda r: "white" if r["white"] == your_name else "black", axis=1)

# ------------------------
# 4. Extract your Elo and opponent Elo
# ------------------------
"""
Assign your Elo and opponent's Elo for each game based on your color.
Takeaway: Allows calculation of rating difference and performance relative to opponent strength.
"""
df["your_elo"] = df.apply(lambda r: r["white_elo"] if r["color"] == "white" else r["black_elo"], axis=1)
df["opponent_elo"] = df.apply(lambda r: r["black_elo"] if r["color"] == "white" else r["white_elo"], axis=1)

# Rating difference (positive = opponent stronger)
df["rating_diff"] = df["opponent_elo"] - df["your_elo"]

# ------------------------
# 5. Convert game results to numerical score
# ------------------------
"""
Convert results (1-0, 0-1, 0.5) into a numeric score from your perspective.
Takeaway: Standardized scoring allows aggregation, correlation, and modeling.
"""
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
print("Counting moves...")

"""
Count moves per game from SAN move list.
Takeaway: Examines whether longer or shorter games correlate with outcomes and identifies typical game lengths.
"""
df["move_count"] = df["moves_san"].apply(lambda x: len(str(x).split()) if pd.notnull(x) else 0)

print("Average game length:", df["move_count"].mean().round(0))
print("Median game length:", df["move_count"].median())
print("Shortest game:", df["move_count"].min())
print("Longest game:", df["move_count"].max())

plt.figure(figsize=(8,4))
plt.hist(df["move_count"], bins=20)
plt.title("Distribution of Game Length (Moves)")
plt.xlabel("Move Count")
plt.ylabel("Count")
plt.show()

correlation = df["move_count"].corr(df["score"])
print("Correlation between game length and score:", correlation)

plt.figure(figsize=(8,4))
plt.scatter(df["move_count"], df["score"])
plt.title("Outcome vs Move Count")
plt.xlabel("Move Count")
plt.ylabel("Score")
plt.show()

df["result_category"] = df["score"].apply(lambda s: "win" if s == 1 else ("loss" if s == 0 else "draw"))
df.boxplot(column="move_count", by="result_category", figsize=(8,5))
plt.title("Game Length by Result Category")
plt.suptitle("")
plt.xlabel("Result")
plt.ylabel("Move Count")
plt.show()

# ===========================================================
# 7. Rating difference & performance analysis
# ===========================================================
print("Performance analysis...")

df["out_rated"] = df["rating_diff"] > 0
print("Performance vs stronger opponents:", df[df["out_rated"]]["score"].mean())
print("Performance vs weaker opponents:", df[~df["out_rated"]]["score"].mean())

plt.figure(figsize=(8,4))
plt.scatter(df["rating_diff"], df["score"], alpha=0.6)
plt.axvline(0, linestyle="dashed", color="black")
plt.title("Performance by Rating Difference")
plt.xlabel("Opponent_Elo - Your_Elo")
plt.ylabel("Score")
plt.show()

# Corrected bins and labels
bins = [-100, -50, -30, -20, -10, 0, 10, 20, 30, 50, 100, 500]  # 12 intervals
labels = ["-100", "-50", "-30", "-20", "-10", "Equal", "+10", "+20", "+30", "+50", "+100"]  # 11 labels

df["rating_bin_fine"] = pd.cut(df["rating_diff"], bins=bins, labels=labels)

rating_bin_stats_fine = df.groupby("rating_bin_fine")["score"].mean()
print("Score by fine-grained rating gap:")
print(rating_bin_stats_fine)

rating_bin_stats_fine.plot(kind="bar", figsize=(10,5))
plt.title("Score by Fine-Grained Rating Difference")
plt.ylabel("Score")
plt.xlabel("Rating Difference Bin")
plt.xticks(rotation=45)
plt.show()




# ===========================================================
# 7.5 Rolling win rate vs game number
# ===========================================================

# ===========================================================
# 7.5 Rolling win rate vs Elo over time
# ===========================================================
"""
Overlay rolling win rate on Elo progression.
Takeaway: Allows you to see whether increases in Elo correspond to improved performance.
"""
# Compute overall rolling win rate (20 games)
df["rolling_win_rate"] = df["score"].rolling(window=20, min_periods=1).mean()

fig, ax1 = plt.subplots(figsize=(12,5))

# Plot Elo on primary y-axis
ax1.plot(df.index, df["your_elo"], color="blue", label="Your Elo", linewidth=2)
ax1.set_xlabel("Game Number")
ax1.set_ylabel("Elo", color="blue")
ax1.tick_params(axis='y', labelcolor="blue")

# Plot rolling win rate on secondary y-axis
ax2 = ax1.twinx()
ax2.plot(df.index, df["rolling_win_rate"], color="green", label="Rolling Win Rate (20 games)", linewidth=2, alpha=0.7)
ax2.set_ylabel("Rolling Win Rate", color="green")
ax2.tick_params(axis='y', labelcolor="green")

# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

plt.title("Elo vs Rolling Win Rate Over Time")
plt.grid(True)
plt.show()


# ===========================================================
# 8. Rolling win-rate when outrated vs higher rated
# ===========================================================
"""
Compute rolling win-rate for games where you were outrated vs higher-rated opponents.
Takeaway: Reveals performance trends and potential improvement over time.
"""
df = df.reset_index(drop=True)
df["score_vs_higher"] = df.apply(lambda r: r["score"] if r["rating_diff"] > 0 else np.nan, axis=1).astype(float)
df["score_vs_lower"]  = df.apply(lambda r: r["score"] if r["rating_diff"] < 0 else np.nan, axis=1).astype(float)

rolling_higher = df["score_vs_higher"].rolling(window=20, min_periods=1).mean()
rolling_lower  = df["score_vs_lower"].rolling(window=20, min_periods=1).mean()

plt.figure(figsize=(12,5))
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
"""
Print basic summary statistics.
Takeaway: Quick overview of your total games, average move counts, and rating differences.
"""
print("Total games:", len(df))
print("Overall performance (score):", df["score"].mean())
print("Average move count:", df["move_count"].mean())
print("Average rating difference:", df["rating_diff"].mean())

# ===========================================================
# 10. Elo progression over time
# ===========================================================
"""
Plot your Elo over time to see trends, growth, and plateaus.
Takeaway: Identify periods of improvement or decline.
"""
df = df.sort_values("datetime").reset_index(drop=True)
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
# 11. Elo progression by color
# ===========================================================
"""
Separate Elo progression for games played as White vs Black.
Takeaway: Understand if your performance differs by color.
"""
df["game_num"] = df.index
plt.figure(figsize=(12,5))
plt.plot(df[df["color"]=="white"]["game_num"], df[df["color"]=="white"]["your_elo"], label="White Elo Progression", linewidth=2)
plt.plot(df[df["color"]=="black"]["game_num"], df[df["color"]=="black"]["your_elo"], label="Black Elo Progression", linewidth=2)
plt.xlabel("Game Number")
plt.ylabel("Your Elo")
plt.title("Elo Progression Over Time (White vs Black)")
plt.legend()
plt.grid(True)
plt.show()

# ===========================================================
# 12. Elo volatility calculation
# ===========================================================
"""
Compute game-to-game Elo changes and standard deviation.
Takeaway: Quantifies how volatile your rating has been over time.
"""
df = df.sort_values("datetime")
df["rating_change"] = df["your_elo"].diff()
elo_volatility = df["rating_change"].std()
print(f"Elo volatility: {elo_volatility:.2f}")

# ===========================================================
# 13. Smoothed Elo curve (rolling mean)
# ===========================================================
"""
Compute rolling mean Elo to visualize long-term trends more clearly.
Takeaway: Smoothed rating curve reduces noise from individual game swings.
"""
df["elo_smooth"] = df["your_elo"].rolling(window=20, center=True).mean()

# ===========================================================
# 14. Identify peaks and troughs
# ===========================================================
"""
Detect local peaks and troughs in your rating.
Takeaway: Highlights best and worst periods in performance.
"""
df["peak"] = (df["your_elo"] > df["your_elo"].shift(1)) & (df["your_elo"] > df["your_elo"].shift(-1))
df["trough"] = (df["your_elo"] < df["your_elo"].shift(1)) & (df["your_elo"] < df["your_elo"].shift(-1))

peaks = df[df["peak"]]
troughs = df[df["trough"]]

print(f"Number of peaks: {len(peaks)}")
print(f"Number of troughs: {len(troughs)}")

# ===========================================================
# 15. Elo progression plot with smoothed curve and highlights
# ===========================================================
"""
Plot your Elo over time with smoothed curve, highlighting peaks and troughs.
Takeaway: Visual summary of growth, decline, and consistency in your rating trajectory.
"""
plt.figure(figsize=(12, 6))
plt.plot(df["datetime"], df["your_elo"], label="Elo", alpha=0.7)
plt.plot(df["datetime"], df["elo_smooth"], label="Smoothed Elo", linewidth=2)
plt.scatter(peaks["datetime"], peaks["your_elo"], label="Peaks")
plt.scatter(troughs["datetime"], troughs["your_elo"], label="Troughs")
plt.xlabel("Date")
plt.ylabel("Your Elo")
plt.title("Elo Progression Over Time")
plt.legend()
plt.tight_layout()
plt.show()
