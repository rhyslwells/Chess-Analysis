"""
explore_analyzer.py
Comprehensive exploration of ChessAnalyzer class functionality.

This script demonstrates ALL analysis methods in the ChessAnalyzer class,
showing how to extract insights from chess game data.

Author: Chess Analysis Dashboard
Date: 2024
Usage: 
    python explore_analyzer.py
    OR in IPython/Jupyter:
    %run explore_analyzer.py
"""

# Import required libraries
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
from datetime import datetime
from pathlib import Path
from src.analyzer import ChessAnalyzer

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set your Chess.com username here
USERNAME = "RhysLWells"

# Path to your CSV data
DATA_DIR = Path("data")
CSV_FILENAME = f"{USERNAME}_games_last_12_months.csv"
CSV_PATH = DATA_DIR / CSV_FILENAME

# Control which sections to run
RUN_CONFIG = {
    'load_data': True,              # Step 1: Load CSV data
    'overall_stats': True,          # Step 2: Overall performance statistics
    'rating_analysis': True,        # Step 3: Rating trends and volatility
    'opponent_strength': True,      # Step 4: Performance vs opponent strength
    'color_performance': True,      # Step 5: White vs Black analysis
    'opening_analysis': True,       # Step 6: Opening repertoire stats
    'time_control': True,           # Step 7: Performance by time control
    'game_length': True,            # Step 8: Game duration analysis
    'results_over_time': True,      # Step 9: Win/Loss/Draw trends
    'recent_games': True,           # Step 10: Recent game review
    'ml_features': True,            # Step 11: ML feature preparation
}

print("=" * 80)
print("CHESS ANALYZER EXPLORATION")
print("=" * 80)
print(f"\nUsername: {USERNAME}")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# =============================================================================
# STEP 1: LOAD DATA
# =============================================================================

if RUN_CONFIG['load_data']:
    print("\n" + "=" * 80)
    print("STEP 1: Loading Chess Game Data")
    print("=" * 80)
    
    print(f"\n Loading data from: {CSV_PATH}")
    
    if not CSV_PATH.exists():
        print(f"\n ERROR: CSV file not found!")
        print(f"   Expected location: {CSV_PATH.absolute()}")
        print(f"\n   Please run explore_data_fetcher.py first to fetch your games.")
        sys.exit(1)
    
    df = pd.read_csv(CSV_PATH)
    
    print(f"\n Data loaded successfully!")
    print(f"  - Total games: {len(df)}")
    print(f"  - Columns: {df.shape[1]}")
    print(f"  - Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    print(f"\n Data overview:")
    print(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  - Rating range: {df['user_rating'].min()} - {df['user_rating'].max()}")
    
    print(f"\n Available columns:")
    for col in df.columns:
        print(f"  - {col}")

# =============================================================================
# INITIALIZE ANALYZER
# =============================================================================

print("\n" + "=" * 80)
print("INITIALIZING CHESS ANALYZER")
print("=" * 80)

print("\n Creating ChessAnalyzer instance...")
print("\nWhat happens during initialization:")
print("  1. Creates a copy of the DataFrame (preserves original)")
print("  2. Computes derived features:")
print("     - rating_diff: Your rating minus opponent's rating")
print("     - opponent_category: Lower/Similar/Higher rated")
print("     - game_num: Chronological game number")
print("     - result_category: Win/Loss/Draw labels")
print("     - move_count: Number of moves (if available)")

analyzer = ChessAnalyzer(df)

print(f"\n Analyzer initialized successfully!")
print(f"  - Base games: {len(analyzer.df)}")
print(f"  - Derived features added: rating_diff, opponent_category, game_num, result_category")

# Show sample of derived features
print(f"\n Sample of enhanced data:")
sample_cols = ['date', 'user_rating', 'opponent_rating', 'rating_diff', 
               'opponent_category', 'result_label']
print(analyzer.df[sample_cols].head(5).to_string(index=False))

# =============================================================================
# STEP 2: OVERALL STATISTICS
# =============================================================================

if RUN_CONFIG['overall_stats']:
    print("\n" + "=" * 80)
    print("STEP 2: get_overall_stats()")
    print("=" * 80)
    
    print("\n Computing overall performance statistics...")
    print("\nWhat this method calculates:")
    print("  - Win/Loss/Draw counts and percentages")
    print("  - Average ratings (you and opponents)")
    print("  - Elo progression (starting to current)")
    
    stats = analyzer.get_overall_stats()
    
    print(f"\n Overall Statistics:")
    print(f"   Total Games: {stats['total_games']}")
    print(f"   Wins: {stats['wins']} ({stats['wins']/stats['total_games']*100:.1f}%)")
    print(f"   Losses: {stats['losses']} ({stats['losses']/stats['total_games']*100:.1f}%)")
    print(f"    Draws: {stats['draws']} ({stats['draws']/stats['total_games']*100:.1f}%)")
    print(f"   Win Rate: {stats['win_rate']:.2f}%")
    
    print(f"\n   Rating Information:")
    print(f"  - Your Average Rating: {stats['avg_user_rating']:.0f}")
    print(f"  - Opponent Average Rating: {stats['avg_opponent_rating']:.0f}")
    print(f"  - Starting Elo: {stats['starting_elo']}")
    print(f"  - Current Elo: {stats['current_elo']}")
    print(f"  - Elo Change: {stats['elo_change']:+.0f}")
    
    if stats['elo_change'] > 0:
        print(f"\n   Rating improved by {stats['elo_change']:.0f} points!")
    elif stats['elo_change'] < 0:
        print(f"\n    Rating decreased by {abs(stats['elo_change']):.0f} points")
    else:
        print(f"\n    Rating remained stable")

# =============================================================================
# STEP 3: RATING ANALYSIS
# =============================================================================

if RUN_CONFIG['rating_analysis']:
    print("\n" + "=" * 80)
    print("STEP 3: Rating Trend & Volatility Analysis")
    print("=" * 80)
    
    print("\n 3A: get_rating_trend()")
    print("\nWhat this returns:")
    print("  - DataFrame with date and user_rating columns")
    print("  - Sorted chronologically for plotting")
    print("  - Ready for time-series visualization")
    
    trend = analyzer.get_rating_trend()
    
    print(f"\n Rating trend data:")
    print(f"  - Data points: {len(trend)}")
    print(f"  - Date range: {trend['date'].min()} to {trend['date'].max()}")
    
    print(f"\n First 10 rating points:")
    print(trend.head(10).to_string(index=False))
    
    print(f"\n Last 10 rating points:")
    print(trend.tail(10).to_string(index=False))
    
    # Volatility
    print("\n" + "-" * 80)
    print(" 3B: get_rating_volatility()")
    print("\nWhat this calculates:")
    print("  - Volatility: Standard deviation of rating changes")
    print("  - Average change: Mean absolute rating swing per game")
    print("  - Max gain/loss: Biggest rating movements")
    
    volatility = analyzer.get_rating_volatility()
    
    print(f"\n Rating Volatility Metrics:")
    print(f"   Volatility (σ): {volatility['volatility']:.2f}")
    print(f"   Average Rating Change: {volatility['avg_rating_change']:.2f}")
    print(f"   Max Rating Gain: {volatility['max_rating_gain']:.0f}")
    print(f"   Max Rating Loss: {volatility['max_rating_loss']:.0f}")
    
    if volatility['volatility'] < 10:
        print(f"\n   Low volatility - rating is stable")
    elif volatility['volatility'] < 20:
        print(f"\n   Moderate volatility - normal fluctuation")
    else:
        print(f"\n    High volatility - rating swings significantly")

# =============================================================================
# STEP 4: OPPONENT STRENGTH ANALYSIS
# =============================================================================

if RUN_CONFIG['opponent_strength']:
    print("\n" + "=" * 80)
    print("STEP 4: get_performance_by_opponent_strength()")
    print("=" * 80)
    
    print("\n Analyzing performance vs different opponent strengths...")
    print("\nOpponent categories:")
    print("  - Lower Rated: Opponent >50 points below you")
    print("  - Similar Rating: Opponent within ±50 points")
    print("  - Higher Rated: Opponent >50 points above you")
    
    opp_strength = analyzer.get_performance_by_opponent_strength()
    
    print(f"\n Performance by Opponent Strength:")
    print(opp_strength.to_string(index=False))
    
    # Analysis
    print(f"\n Insights:")
    for _, row in opp_strength.iterrows():
        print(f"\n  {row['category']}:")
        print(f"    - Games: {row['games']}")
        print(f"    - Wins: {row['wins']}")
        print(f"    - Win Rate: {row['win_rate']:.1f}%")
        print(f"    - Avg Score: {row['avg_score']:.3f} (0=loss, 0.5=draw, 1=win)")
    
    # Expected performance check
    if len(opp_strength) == 3:
        lower_wr = opp_strength[opp_strength['category'] == 'Lower Rated']['win_rate'].values[0]
        higher_wr = opp_strength[opp_strength['category'] == 'Higher Rated']['win_rate'].values[0]
        
        if lower_wr > higher_wr:
            print(f"\n   Expected pattern: Better vs lower-rated ({lower_wr:.1f}%) than higher-rated ({higher_wr:.1f}%)")
        else:
            print(f"\n    Unexpected: Better vs higher-rated ({higher_wr:.1f}%) than lower-rated ({lower_wr:.1f}%)")

# =============================================================================
# STEP 5: COLOR PERFORMANCE
# =============================================================================

if RUN_CONFIG['color_performance']:
    print("\n" + "=" * 80)
    print("STEP 5: get_color_performance()")
    print("=" * 80)
    
    print("\n Analyzing performance by color...")
    print("\nWhat this compares:")
    print("  - Win rate when playing White vs Black")
    print("  - Total games with each color")
    print("  - Average score (accounting for draws)")
    
    color_perf = analyzer.get_color_performance()
    
    print(f"\n Color Performance:")
    print(color_perf.to_string(index=False))
    
    # Detailed analysis
    white_row = color_perf[color_perf['color'] == 'White'].iloc[0]
    black_row = color_perf[color_perf['color'] == 'Black'].iloc[0]
    
    print(f"\n Detailed Breakdown:")
    print(f"\n   White:")
    print(f"    - Games: {white_row['games']}")
    print(f"    - Wins: {white_row['wins']}")
    print(f"    - Win Rate: {white_row['win_rate']}%")
    print(f"    - Avg Score: {white_row['avg_score']}")
    
    print(f"\n   Black:")
    print(f"    - Games: {black_row['games']}")
    print(f"    - Wins: {black_row['wins']}")
    print(f"    - Win Rate: {black_row['win_rate']}%")
    print(f"    - Avg Score: {black_row['avg_score']}")
    
    diff = white_row['win_rate'] - black_row['win_rate']
    print(f"\n   Difference: {abs(diff):.1f}% {'(White better)' if diff > 0 else '(Black better)' if diff < 0 else '(Equal)'}")
    
    if abs(diff) < 5:
        print(f"   Balanced performance with both colors")
    elif diff > 0:
        print(f"   Stronger with White pieces")
    else:
        print(f"   Stronger with Black pieces")

# =============================================================================
# STEP 6: OPENING ANALYSIS
# =============================================================================

if RUN_CONFIG['opening_analysis']:
    print("\n" + "=" * 80)
    print("STEP 6: get_opening_stats(top_n=10)")
    print("=" * 80)
    
    print("\n Analyzing opening repertoire...")
    print("\nWhat this identifies:")
    print("  - Most frequently played openings")
    print("  - Win rate with each opening")
    print("  - Sample size for statistical significance")
    
    openings = analyzer.get_opening_stats(top_n=15)
    
    print(f"\n Top 15 Openings by Frequency:")
    print(openings.to_string(index=False))
    
    # Identify best/worst openings with sufficient games
    min_games = 5
    significant = openings[openings['games'] >= min_games]
    
    if len(significant) > 0:
        best_opening = significant.loc[significant['win_rate'].idxmax()]
        worst_opening = significant.loc[significant['win_rate'].idxmin()]
        
        print(f"\n Openings with ≥{min_games} games:")
        print(f"\n   Best Performing:")
        print(f"    - {best_opening['opening']}")
        print(f"    - Games: {best_opening['games']:.0f}")
        print(f"    - Wins: {best_opening['wins']:.0f}")
        print(f"    - Win Rate: {best_opening['win_rate']:.1f}%")
        
        print(f"\n    Worst Performing:")
        print(f"    - {worst_opening['opening']}")
        print(f"    - Games: {worst_opening['games']:.0f}")
        print(f"    - Wins: {worst_opening['wins']:.0f}")
        print(f"    - Win Rate: {worst_opening['win_rate']:.1f}%")
    
    # Diversity metric
    total_openings = analyzer.df['opening'].nunique()
    print(f"\n   Repertoire Diversity:")
    print(f"    - Total unique openings: {total_openings}")
    print(f"    - Top opening frequency: {openings.iloc[0]['games']:.0f}/{len(analyzer.df)} ({openings.iloc[0]['games']/len(analyzer.df)*100:.1f}%)")

# =============================================================================
# STEP 7: TIME CONTROL ANALYSIS
# =============================================================================

if RUN_CONFIG['time_control']:
    print("\n" + "=" * 80)
    print("STEP 7: get_time_control_stats()")
    print("=" * 80)
    
    print("\n⏱  Analyzing performance by time control...")
    print("\nTime control categories:")
    print("  - Bullet: <3 minutes")
    print("  - Blitz: 3-10 minutes")
    print("  - Rapid: 10-60 minutes")
    print("  - Daily: Correspondence chess")
    
    tc_stats = analyzer.get_time_control_stats()
    
    print(f"\n Time Control Statistics:")
    print(tc_stats.to_string(index=False))
    
    # Analysis
    print(f"\n Breakdown:")
    for _, row in tc_stats.iterrows():
        print(f"\n  {row['time_control'].capitalize()}:")
        print(f"    - Games: {row['games']:.0f}")
        print(f"    - Wins: {row['wins']:.0f}")
        print(f"    - Win Rate: {row['win_rate']}%")
    
    if len(tc_stats) > 1:
        best_tc = tc_stats.loc[tc_stats['win_rate'].idxmax()]
        print(f"\n   Best time control: {best_tc['time_control']} ({best_tc['win_rate']}% win rate)")

# =============================================================================
# STEP 8: GAME LENGTH ANALYSIS
# =============================================================================

if RUN_CONFIG['game_length']:
    print("\n" + "=" * 80)
    print("STEP 8: Game Duration Analysis")
    print("=" * 80)
    
    print("\n⏱  8A: get_game_length_stats()")
    print("\nWhat this analyzes:")
    print("  - Average game duration (wall-clock time)")
    print("  - Range of game lengths")
    print("  - Correlation between length and results")
    
    length_stats = analyzer.get_game_length_stats()
    
    print(f"\n Game Length Statistics:")
    print(f"  ⏱  Average: {length_stats['average']/60:.1f} minutes ({length_stats['average']:.0f}s)")
    print(f"  ⏱  Median: {length_stats['median']/60:.1f} minutes ({length_stats['median']:.0f}s)")
    print(f"  ⏱  Shortest: {length_stats['shortest']/60:.1f} minutes ({length_stats['shortest']:.0f}s)")
    print(f"  ⏱  Longest: {length_stats['longest']/60:.1f} minutes ({length_stats['longest']:.0f}s)")
    print(f"   Length-Result Correlation: {length_stats['length_result_corr']:.3f}")
    
    # Interpret correlation
    corr = length_stats['length_result_corr']
    print(f"\n   Interpretation:")
    if abs(corr) < 0.1:
        print(f"    - Negligible correlation ({corr:.3f})")
        print(f"    - Game length doesn't predict outcome")
    elif corr > 0:
        print(f"    - Positive correlation ({corr:.3f})")
        print(f"    - Longer games tend to be wins")
    else:
        print(f"    - Negative correlation ({corr:.3f})")
        print(f"    - Shorter games tend to be wins")
    
    # By result
    print("\n" + "-" * 80)
    print(" 8B: get_game_length_by_result()")
    
    length_by_result = analyzer.get_game_length_by_result()
    
    print(f"\n Game Duration by Outcome:")
    print(length_by_result.to_string(index=False))
    
    print(f"\n Insights:")
    for _, row in length_by_result.iterrows():
        avg_min = row['Average Length (s)'] / 60
        print(f"  {row['Result']}: {avg_min:.1f} min average ({row['Games']} games)")

# =============================================================================
# STEP 9: RESULTS OVER TIME
# =============================================================================

if RUN_CONFIG['results_over_time']:
    print("\n" + "=" * 80)
    print("STEP 9: get_results_over_time(period='M')")
    print("=" * 80)
    
    print("\n Analyzing win/loss/draw trends over time...")
    print("\nPeriod options:")
    print("  - 'D': Daily")
    print("  - 'W': Weekly")
    print("  - 'M': Monthly (default)")
    
    results_monthly = analyzer.get_results_over_time(period='M')
    
    print(f"\n Results Over Time (Monthly):")
    print(results_monthly.to_string())
    
    # Calculate monthly win rates
    print(f"\n Monthly Win Rates:")
    results_monthly['Total'] = results_monthly.sum(axis=1)
    results_monthly['Win Rate %'] = (results_monthly['Wins'] / results_monthly['Total'] * 100).round(1)
    
    print(results_monthly[['Wins', 'Losses', 'Draws', 'Total', 'Win Rate %']].to_string())
    
    # Trend analysis
    if len(results_monthly) > 1:
        first_month_wr = results_monthly['Win Rate %'].iloc[0]
        last_month_wr = results_monthly['Win Rate %'].iloc[-1]
        trend = last_month_wr - first_month_wr
        
        print(f"\n   Trend Analysis:")
        print(f"    - First month win rate: {first_month_wr:.1f}%")
        print(f"    - Last month win rate: {last_month_wr:.1f}%")
        print(f"    - Change: {trend:+.1f}%")

# =============================================================================
# STEP 10: RECENT GAMES
# =============================================================================

if RUN_CONFIG['recent_games']:
    print("\n" + "=" * 80)
    print("STEP 10: get_recent_games(n=10)")
    print("=" * 80)
    
    print("\n Fetching most recent games...")
    print("\nWhat this returns:")
    print("  - Last N games played (sorted by timestamp)")
    print("  - Useful for recent performance review")
    
    recent = analyzer.get_recent_games(n=10)
    
    print(f"\n 10 Most Recent Games:")
    recent_display = recent[['date', 'user_color', 'user_rating', 'opponent_rating', 
                             'result_label', 'opening']].copy()
    print(recent_display.to_string(index=False))
    
    # Recent streak analysis
    recent_results = recent['result'].values
    recent_wins = (recent_results == 1).sum()
    recent_losses = (recent_results == 0).sum()
    recent_wr = (recent_wins / len(recent)) * 100
    
    print(f"\n Recent Performance (Last 10 games):")
    print(f"  - Wins: {recent_wins}")
    print(f"  - Losses: {recent_losses}")
    print(f"  - Draws: {len(recent) - recent_wins - recent_losses}")
    print(f"  - Win Rate: {recent_wr:.1f}%")

# =============================================================================
# STEP 11: ML FEATURE PREPARATION
# =============================================================================

if RUN_CONFIG['ml_features']:
    print("\n" + "=" * 80)
    print("STEP 11: prepare_ml_features()")
    print("=" * 80)
    
    print("\n Preparing features for machine learning...")
    print("\nWhat this creates:")
    print("  - X: Feature matrix (user_rating, opponent_rating, rating_diff, is_white)")
    print("  - y: Target vector (1 for win, 0 for loss/draw)")
    print("  - Binary classification setup for win prediction")
    
    X, y = analyzer.prepare_ml_features()
    
    print(f"\n ML Features Prepared:")
    print(f"   Feature matrix shape: {X.shape}")
    print(f"   Target vector shape: {y.shape}")
    print(f"   Features: {list(X.columns)}")
    
    print(f"\n Sample features:")
    print(X.head(10).to_string(index=False))
    
    print(f"\n Target distribution:")
    print(f"  - Wins (y=1): {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
    print(f"  - Not Wins (y=0): {len(y) - y.sum()} ({(len(y)-y.sum())/len(y)*100:.1f}%)")
    
    print(f"\n Feature statistics:")
    print(X.describe().round(2).to_string())

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("EXPLORATION COMPLETE!")
print("=" * 80)

print("\n Methods demonstrated:")
methods = [
    "1. __init__() - Initialize and compute derived features",
    "2. get_overall_stats() - Overall performance metrics",
    "3. get_rating_trend() - Rating progression over time",
    "4. get_rating_volatility() - Rating stability metrics",
    "5. get_performance_by_opponent_strength() - Win rates vs different opponents",
    "6. get_color_performance() - White vs Black analysis",
    "7. get_opening_stats() - Opening repertoire analysis",
    "8. get_time_control_stats() - Performance by time control",
    "9. get_game_length_stats() - Duration analysis",
    "10. get_game_length_by_result() - Duration by outcome",
    "11. get_results_over_time() - Temporal trend analysis",
    "12. get_recent_games() - Recent game review",
    "13. prepare_ml_features() - ML feature engineering"
]
for method in methods:
    print(f"  {method}")

print("\n Key insights discovered:")
insights = [
    " Overall performance and Elo progression",
    " Rating stability and volatility patterns",
    " Performance against different opponent strengths",
    " Color preferences and tendencies",
    " Opening repertoire effectiveness",
    " Time control strengths",
    " Game duration patterns and correlations",
    " Win/loss trends over time",
    " Recent form analysis",
    " Features ready for ML modeling"
]
for insight in insights:
    print(f"  {insight}")

print("\n Next steps:")
print("  1. Use these insights for dashboard visualizations")
print("  2. Feed ML features into ChessPredictor for win prediction")
print("  3. Identify areas for improvement in your game")
print("  4. Track progress over time with periodic analysis")

print("\n Analysis complete for:")
if 'stats' in locals():
    print(f"  - {stats['total_games']} total games")
    print(f"  - Win rate: {stats['win_rate']:.1f}%")
    print(f"  - Rating range: {stats['starting_elo']} → {stats['current_elo']} ({stats['elo_change']:+.0f})")

print("\n" + "=" * 80)