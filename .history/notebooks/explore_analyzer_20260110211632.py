Store any created images into a subfolder 'images' within the current directory.

i care about:
fine_grained_rating_performance.png - we should turn the bins from 10 to 5.
opening_repertoire.png
rating_progression.png


im not interested in :
rating_peaks_troughs.png
opponent_strength_performance.png
rating_peaks_troughs.png


"""
explore_analyzer.py
Interactive exploration of ChessAnalyzer features using real data.

This script demonstrates all the analysis capabilities of the ChessAnalyzer class
using rhyslwells as the example user. It can be run directly or used interactively
in a Jupyter notebook or IPython session.

Usage:
    python explore_analyzer.py
    
Or in IPython/Jupyter:
    %run explore_analyzer.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Add parent directory to path


import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
from src.data_fetcher import ChessDataFetcher
from src.analyzer import ChessAnalyzer
import seaborn as sns
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Import our custom modules

# Set up plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Configuration
USERNAME = "rhyslwells"
FETCH_NEW_DATA = False  # Set to True to fetch fresh data from Chess.com

print("=" * 70)
print("CHESS GAME ANALYZER EXPLORATION")
print("=" * 70)
print(f"\nAnalyzing games for user: {USERNAME}")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ===========================================================
# STEP 1: Load or Fetch Data
# ===========================================================
print("\n" + "=" * 70)
print("STEP 1: DATA LOADING")
print("=" * 70)

fetcher = ChessDataFetcher()

if FETCH_NEW_DATA:
    print(f"\n📥 Fetching new data from Chess.com for {USERNAME}...")
    print("This may take a few minutes depending on game history...\n")
    
    # Option 1: Fetch recent games (last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    games = fetcher.fetch_multiple_months(USERNAME, start_date, end_date)
    df = fetcher.process_and_save(USERNAME, games, mode='json')
    
    # Option 2: Fetch ALL games (uncomment to use)
    # df = fetcher.fetch_and_process_all(USERNAME)
    
    print(f"✅ Successfully fetched {len(df)} games")
else:
    print(f"\n📂 Loading existing data for {USERNAME}...")
    df = fetcher.load_existing_data(USERNAME)
    
    if df is None:
        print(f"❌ No existing data found for {USERNAME}")
        print("Set FETCH_NEW_DATA = True to download games from Chess.com")
        exit()
    
    print(f"✅ Loaded {len(df)} games from CSV")

print(f"\nDataset overview:")
print(f"  - Total games: {len(df)}")
print(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
print(f"  - Columns: {', '.join(df.columns)}")

# ===========================================================
# STEP 2: Initialize Analyzer
# ===========================================================
print("\n" + "=" * 70)
print("STEP 2: INITIALIZE ANALYZER")
print("=" * 70)

print("\n🔧 Creating ChessAnalyzer instance...")
print("The analyzer automatically computes derived features:")
print("  - Rating differences")
print("  - Opponent strength categories")
print("  - Game chronological numbering")
print("  - Move counts (if available)")

analyzer = ChessAnalyzer(df)

print("✅ Analyzer initialized successfully")

# ===========================================================
# STEP 3: Overall Statistics
# ===========================================================
print("\n" + "=" * 70)
print("STEP 3: OVERALL PERFORMANCE STATISTICS")
print("=" * 70)

print("\n📊 Computing overall statistics...")
stats = analyzer.get_overall_stats()

print("\n" + "-" * 70)
print("SUMMARY STATISTICS")
print("-" * 70)
print(f"Total Games:          {stats['total_games']:,}")
print(f"Wins:                 {stats['wins']:,} ({stats['win_rate']:.1f}%)")
print(f"Losses:               {stats['losses']:,}")
print(f"Draws:                {stats['draws']:,}")
print(f"\nAverage Your Rating:  {stats['avg_user_rating']:.0f}")
print(f"Average Opp Rating:   {stats['avg_opponent_rating']:.0f}")
print(f"\nStarting Elo:         {stats['starting_elo']:.0f}")
print(f"Current Elo:          {stats['current_elo']:.0f}")
print(f"Rating Change:        {stats['elo_change']:+.0f}")
print("-" * 70)

# ===========================================================
# STEP 4: Performance by Opponent Strength
# ===========================================================
print("\n" + "=" * 70)
print("STEP 4: PERFORMANCE BY OPPONENT STRENGTH")
print("=" * 70)

print("\n⚔️ Analyzing performance vs different opponent levels...")
print("Categories:")
print("  - Lower Rated:  Opponent 100+ points below you")
print("  - Similar:      Within ±100 points")
print("  - Higher Rated: Opponent 100+ points above you")

opp_strength = analyzer.get_performance_by_opponent_strength()
print("\n" + opp_strength.to_string(index=False))

# Visualize
plt.figure(figsize=(10, 5))
plt.bar(opp_strength['category'], opp_strength['win_rate'], 
        color=['#2ecc71', '#f39c12', '#e74c3c'])
plt.title('Win Rate by Opponent Strength', fontsize=14, fontweight='bold')
plt.xlabel('Opponent Category')
plt.ylabel('Win Rate (%)')
plt.ylim(0, 100)
for i, (cat, rate) in enumerate(zip(opp_strength['category'], opp_strength['win_rate'])):
    plt.text(i, rate + 2, f'{rate:.1f}%', ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig('opponent_strength_performance.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: opponent_strength_performance.png")

# ===========================================================
# STEP 5: Fine-Grained Rating Analysis
# ===========================================================
print("\n" + "=" * 70)
print("STEP 5: FINE-GRAINED RATING DIFFERENCE ANALYSIS")
print("=" * 70)

print("\n🔬 Analyzing performance across narrow rating bands...")
print("This shows how small rating differences affect your win probability")

fine_perf = analyzer.get_fine_grained_rating_performance()
print("\n" + fine_perf.to_string(index=False))

# Visualize
plt.figure(figsize=(12, 6))
plt.bar(range(len(fine_perf)), fine_perf['win_rate'], color='skyblue', edgecolor='navy')
plt.xticks(range(len(fine_perf)), fine_perf['rating_bin'], rotation=45)
plt.axhline(y=50, color='red', linestyle='--', label='50% (Even odds)')
plt.title('Win Rate by Fine-Grained Rating Difference', fontsize=14, fontweight='bold')
plt.xlabel('Rating Difference Bin')
plt.ylabel('Win Rate (%)')
plt.legend()
plt.tight_layout()
plt.savefig('fine_grained_rating_performance.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: fine_grained_rating_performance.png")

# ===========================================================
# STEP 6: Opening Analysis
# ===========================================================
print("\n" + "=" * 70)
print("STEP 6: OPENING REPERTOIRE ANALYSIS")
print("=" * 70)

print("\n♟️ Analyzing your most-played openings...")
opening_stats = analyzer.get_opening_stats(top_n=10)
print("\n" + opening_stats.to_string(index=False))

print("\n💡 Insights:")
best_opening = opening_stats.iloc[0]
print(f"  - Most played: {best_opening['opening']} ({best_opening['games']:.0f} games)")
highest_wr = opening_stats.loc[opening_stats['win_rate'].idxmax()]
print(f"  - Best win rate: {highest_wr['opening']} ({highest_wr['win_rate']:.1f}%)")

# Visualize
plt.figure(figsize=(12, 6))
colors = plt.cm.RdYlGn(opening_stats['win_rate'] / 100)
plt.barh(range(len(opening_stats)), opening_stats['games'], color=colors)
plt.yticks(range(len(opening_stats)), opening_stats['opening'])
plt.xlabel('Games Played')
plt.title('Top 10 Openings (colored by win rate)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('opening_repertoire.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: opening_repertoire.png")

# ===========================================================
# STEP 7: Rating Progression
# ===========================================================
print("\n" + "=" * 70)
print("STEP 7: RATING PROGRESSION OVER TIME")
print("=" * 70)

print("\n📈 Tracking your rating journey...")
rating_trend = analyzer.get_rating_trend()
rating_smoothed = analyzer.get_rating_trend_with_smoothing(window=20)

# Visualize
plt.figure(figsize=(14, 6))
plt.plot(rating_trend['date'], rating_trend['user_rating'], 
         alpha=0.4, color='gray', label='Raw Rating')
plt.plot(rating_smoothed['date'], rating_smoothed['elo_smooth'], 
         color='blue', linewidth=2, label='Smoothed (20-game avg)')
plt.xlabel('Date')
plt.ylabel('Rating')
plt.title('Rating Progression Over Time', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('rating_progression.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: rating_progression.png")

# ===========================================================
# STEP 8: Rating Volatility
# ===========================================================
print("\n" + "=" * 70)
print("STEP 8: RATING VOLATILITY ANALYSIS")
print("=" * 70)

print("\n📊 Computing rating stability metrics...")
volatility = analyzer.get_rating_volatility()

print("\n" + "-" * 70)
print("VOLATILITY METRICS")
print("-" * 70)
print(f"Rating Volatility (std):  {volatility['volatility']:.2f}")
print(f"Avg Rating Change/Game:   {volatility['avg_rating_change']:.2f}")
print(f"Max Single-Game Gain:     +{volatility['max_rating_gain']:.0f}")
print(f"Max Single-Game Loss:     {volatility['max_rating_loss']:.0f}")
print("-" * 70)

print("\n💡 Interpretation:")
if volatility['volatility'] > 30:
    print("  - HIGH volatility: Your rating swings significantly between games")
    print("  - This suggests inconsistent performance or playing varied opponents")
elif volatility['volatility'] > 15:
    print("  - MODERATE volatility: Normal rating fluctuations")
else:
    print("  - LOW volatility: Very stable, consistent performance")

# ===========================================================
# STEP 9: Peaks and Troughs
# ===========================================================
print("\n" + "=" * 70)
print("STEP 9: RATING PEAKS AND TROUGHS")
print("=" * 70)

print("\n🏔️ Identifying your best and worst rating periods...")
peaks, troughs = analyzer.get_peaks_and_troughs()

print(f"\nFound {len(peaks)} peaks and {len(troughs)} troughs")

if len(peaks) > 0:
    best_peak = peaks.loc[peaks['user_rating'].idxmax()]
    print(f"\n🎯 Best Rating Peak:")
    print(f"  - Rating: {best_peak['user_rating']:.0f}")
    print(f"  - Date: {best_peak['date']}")
    print(f"  - Game #{best_peak['game_num']:.0f}")

if len(troughs) > 0:
    worst_trough = troughs.loc[troughs['user_rating'].idxmin()]
    print(f"\n📉 Lowest Rating Trough:")
    print(f"  - Rating: {worst_trough['user_rating']:.0f}")
    print(f"  - Date: {worst_trough['date']}")
    print(f"  - Game #{worst_trough['game_num']:.0f}")

# Visualize with peaks and troughs
plt.figure(figsize=(14, 6))
plt.plot(rating_trend['date'], rating_trend['user_rating'], 
         alpha=0.6, color='blue', label='Rating')
plt.scatter(peaks['date'], peaks['user_rating'], 
           color='green', s=100, marker='^', label='Peaks', zorder=5)
plt.scatter(troughs['date'], troughs['user_rating'], 
           color='red', s=100, marker='v', label='Troughs', zorder=5)
plt.xlabel('Date')
plt.ylabel('Rating')
plt.title('Rating with Peaks and Troughs Highlighted', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('rating_peaks_troughs.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: rating_peaks_troughs.png")

# ===========================================================
# STEP 10: Rolling Win Rate
# ===========================================================
print("\n" + "=" * 70)
print("STEP 10: ROLLING WIN RATE ANALYSIS")
print("=" * 70)

print("\n📈 Computing 20-game rolling win rate...")
rolling_wr = analyzer.get_rolling_win_rate(window=20)

# Visualize dual-axis: Rating + Win Rate
fig, ax1 = plt.subplots(figsize=(14, 6))

ax1.plot(rolling_wr['date'], rolling_wr['user_rating'], 
         color='blue', linewidth=2, label='Rating')
ax1.set_xlabel('Date')
ax1.set_ylabel('Rating', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

ax2 = ax1.twinx()
ax2.plot(rolling_wr['date'], rolling_wr['rolling_win_rate'] * 100, 
         color='green', linewidth=2, alpha=0.7, label='Rolling Win Rate')
ax2.set_ylabel('Rolling Win Rate (%)', color='green')
ax2.tick_params(axis='y', labelcolor='green')
ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5)

plt.title('Rating vs Rolling Win Rate Over Time', fontsize=14, fontweight='bold')
fig.tight_layout()
plt.savefig('rating_vs_winrate.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: rating_vs_winrate.png")

print("\n💡 Analysis:")
correlation = rolling_wr['user_rating'].corr(rolling_wr['rolling_win_rate'])
print(f"  - Correlation between rating and win rate: {correlation:.3f}")
if correlation > 0.5:
    print("  - STRONG positive correlation: Higher rating = better results")
elif correlation > 0.2:
    print("  - MODERATE positive correlation: Rating and performance somewhat aligned")
else:
    print("  - WEAK correlation: Rating doesn't strongly predict short-term performance")

# ===========================================================
# STEP 11: Performance vs Opponent Type (Rolling)
# ===========================================================
print("\n" + "=" * 70)
print("STEP 11: ROLLING PERFORMANCE BY OPPONENT TYPE")
print("=" * 70)

print("\n⚔️ Comparing rolling performance vs higher/lower rated opponents...")
rolling_split = analyzer.get_rolling_performance_by_rating(window=20)

plt.figure(figsize=(14, 6))
plt.plot(rolling_split['date'], rolling_split['vs_higher_rated'] * 100, 
         label='vs Higher Rated', linewidth=2, color='red', alpha=0.7)
plt.plot(rolling_split['date'], rolling_split['vs_lower_rated'] * 100, 
         label='vs Lower Rated', linewidth=2, color='green', alpha=0.7)
plt.axhline(y=50, color='black', linestyle='--', alpha=0.5, label='50%')
plt.xlabel('Date')
plt.ylabel('Rolling Win Rate (%)')
plt.title('Rolling Win Rate by Opponent Strength (20-game window)', 
          fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('rolling_by_opponent_type.png', dpi=300, bbox_inches='tight')
print("\n📊 Chart saved: rolling_by_opponent_type.png")

# ===========================================================
# STEP 12: Color Performance
# ===========================================================
print("\n" + "=" * 70)
print("STEP 12: PERFORMANCE BY COLOR")
print("=" * 70)

print("\n⚪⚫ Analyzing White vs Black performance...")
color_perf = analyzer.get_color_performance()
print("\n" + color_perf.to_string(index=False))

white_wr = color_perf[color_perf['color'] == 'White']['win_rate'].values[0]
black_wr = color_perf[color_perf['color'] == 'Black']['win_rate'].values[0]

print(f"\n💡 Color Advantage: {abs(white_wr - black_wr):.1f}% difference")
if white_wr > black_wr + 5:
    print("  - You perform significantly better as White")
elif black_wr > white_wr + 5:
    print("  - You perform significantly better as Black")
else:
    print("  - Fairly balanced performance with both colors")

# ===========================================================
# STEP 13: Game Length Analysis (if available)
# ===========================================================
print("\n" + "=" * 70)
print("STEP 13: GAME LENGTH ANALYSIS")
print("=" * 70)

length_stats = analyzer.get_game_length_stats()

if length_stats is not None:
    print("\n📏 Analyzing game length patterns...")
    print("\n" + "-" * 70)
    print("GAME LENGTH STATISTICS")
    print("-" * 70)
    print(f"Average Game Length:  {length_stats['avg_game_length']:.0f} moves")
    print(f"Median Game Length:   {length_stats['median_game_length']:.0f} moves")
    print(f"Shortest Game:        {length_stats['shortest_game']:.0f} moves")
    print(f"Longest Game:         {length_stats['longest_game']:.0f} moves")
    print(f"Length-Score Correlation: {length_stats['length_score_correlation']:.3f}")
    print("-" * 70)
    
    print("\n💡 Interpretation:")
    corr = length_stats['length_score_correlation']
    if corr > 0.1:
        print("  - You tend to perform BETTER in longer games (endgame strength)")
    elif corr < -0.1:
        print("  - You tend to perform BETTER in shorter games (tactical prowess)")
    else:
        print("  - Game length doesn't significantly affect your results")
    
    # Analyze by result
    length_by_result = analyzer.get_game_length_by_result()
    print("\n" + length_by_result.to_string(index=False))
    
    # Visualize
    plt.figure(figsize=(10, 6))
    df_plot = analyzer.df
    df_plot.boxplot(column='move_count', by='result_category', figsize=(10, 6))
    plt.suptitle('')
    plt.title('Game Length Distribution by Result', fontsize=14, fontweight='bold')
    plt.xlabel('Result')
    plt.ylabel('Move Count')
    plt.tight_layout()
    plt.savefig('game_length_by_result.png', dpi=300, bbox_inches='tight')
    print("\n📊 Chart saved: game_length_by_result.png")
else:
    print("\n⚠️ Game length analysis not available (no move data)")
    print("  Fetch data using PGN mode to get move sequences")

# ===========================================================
# STEP 14: Time Control Performance
# ===========================================================
print("\n" + "=" * 70)
print("STEP 14: PERFORMANCE BY TIME CONTROL")
print("=" * 70)

print("\n⏱️ Analyzing performance across different time formats...")
tc_stats = analyzer.get_time_control_stats()
print("\n" + tc_stats.to_string(index=False))

if len(tc_stats) > 0:
    best_tc = tc_stats.loc[tc_stats['win_rate'].idxmax()]
    print(f"\n🎯 Best Time Control: {best_tc['time_control']}")
    print(f"  - Win Rate: {best_tc['win_rate']:.1f}%")
    print(f"  - Games Played: {best_tc['games']:.0f}")

# ===========================================================
# FINAL SUMMARY
# ===========================================================
print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)

print("\n📁 Generated Files:")
files = [
    'opponent_strength_performance.png',
    'fine_grained_rating_performance.png',
    'opening_repertoire.png',
    'rating_progression.png',
    'rating_peaks_troughs.png',
    'rating_vs_winrate.png',
    'rolling_by_opponent_type.png'
]
if length_stats is not None:
    files.append('game_length_by_result.png')

for f in files:
    print(f"  ✅ {f}")

print("\n🎉 Exploration complete! Review the charts and statistics above.")
print("\n💡 Next Steps:")
print("  1. Review the generated PNG files for visual insights")
print("  2. Identify patterns in your play (strengths/weaknesses)")
print("  3. Use insights to improve your chess strategy")
print("  4. Re-run this script periodically to track improvement")

print("\n" + "=" * 70)