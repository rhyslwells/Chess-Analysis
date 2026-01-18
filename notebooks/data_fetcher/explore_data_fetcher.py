"""
explore_data_fetcher.py
Comprehensive exploration of ChessDataFetcher class functionality.

This script demonstrates ALL methods in the ChessDataFetcher class,
showing how to fetch, parse, and process chess game data from Chess.com.

Author: Chess Analysis Dashboard
Date: 2024
Usage: 
    python explore_data_fetcher.py
    OR in IPython/Jupyter:
    %run explore_data_fetcher.py
"""

# Import required libraries
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
from src.data_fetcher import ChessDataFetcher

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set your Chess.com username here
USERNAME = "RhysLWells"

# Control which sections to run (useful for testing specific features)
RUN_CONFIG = {
    'get_archives': True,           # Step 1: Get list of available archives
    'fetch_single_archive': False,  # Step 2: Fetch from specific archive URL
    'fetch_all_games': True,        # Step 3: Fetch ALL games (only if CSV doesn't exist)
    'fetch_single_month': False,    # Step 4: Fetch games for one month
    'fetch_date_range': False,      # Step 5: Fetch games for date range
    'get_current_elo': True,        # Step 6: Get current player stats
    'process_and_save': True,       # Step 7: Process and save to CSV (only if fetched)
    'validation_report': True,      # Step 8: View duration validation report
    'load_existing': True,          # Step 9: Load existing CSV
}

# Data fetching configuration
FETCH_LIMIT_MONTHS = 12  # Fetch last N months (None = all history)
OUTPUT_DIR = Path("data")
CSV_FILENAME = f"{USERNAME}_games_last_{FETCH_LIMIT_MONTHS}_months.csv"
FORCE_REFETCH = False  # Set to True to ignore existing CSV and fetch fresh data

print("=" * 80)
print("CHESS DATA FETCHER EXPLORATION")
print("=" * 80)
print(f"\nUsername: {USERNAME}")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# =============================================================================
# INITIALIZE DATA FETCHER
# =============================================================================

print("\n" + "=" * 80)
print("INITIALIZATION")
print("=" * 80)

print("\n Creating ChessDataFetcher instance...")
print("\nWhat happens during initialization:")
print("  1. Sets base URL for Chess.com API")
print("  2. Configures User-Agent header (required for API etiquette)")
print("  3. Initializes validation counters for game duration tracking")
print("  4. Prepares to handle edge cases (negative durations, timezone issues)")

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"\n Output directory: {OUTPUT_DIR.absolute()}")

fetcher = ChessDataFetcher()

print(f"\n Fetcher initialized successfully!")
print(f"  - Base URL: {fetcher.BASE_URL}")
print(f"  - User-Agent: {fetcher.HEADERS['User-Agent']}")
print(f"  - Duration validation counters ready")
print(f"  - Will fetch last {FETCH_LIMIT_MONTHS} months of data")

# =============================================================================
# STEP 1: GET_AVAILABLE_ARCHIVES()
# =============================================================================

if RUN_CONFIG['get_archives']:
    print("\n" + "=" * 80)
    print("STEP 1: get_available_archives(username)")
    print("=" * 80)
    
    print(f"\n Fetching list of available archives for {USERNAME}...")
    print("\nWhat this method does:")
    print("  - Calls: GET https://api.chess.com/pub/player/{username}/games/archives")
    print("  - Returns: List of URLs pointing to monthly game archives")
    print("  - Purpose: Discover ALL available data before downloading")
    print("  - Benefit: Allows you to see complete game history at a glance")
    
    archives = fetcher.get_available_archives(USERNAME)
    
    print(f"\n Found {len(archives)} monthly archives")
    
    if archives:
        print("\n First 5 archives:")
        for i, archive in enumerate(archives[:5], 1):
            parts = archive.split('/')
            year, month = parts[-2], parts[-1]
            print(f"  {i}. {year}-{month}: {archive}")
        
        print(f"\n Last 5 archives:")
        for i, archive in enumerate(archives[-5:], len(archives)-4):
            parts = archive.split('/')
            year, month = parts[-2], parts[-1]
            print(f"  {i}. {year}-{month}: {archive}")
        
        first_archive = archives[0].split('/')
        last_archive = archives[-1].split('/')
        print(f"\n Archive summary:")
        print(f"  - Earliest: {first_archive[-2]}-{first_archive[-1]}")
        print(f"  - Latest: {last_archive[-2]}-{last_archive[-1]}")
        print(f"  - Total months: {len(archives)}")
        
        # Store for later use
        available_archives = archives
    else:
        print(" No archives found (check username)")
        available_archives = []

# =============================================================================
# STEP 2: FETCH_GAMES_FROM_ARCHIVE_URL()
# =============================================================================

if RUN_CONFIG['fetch_single_archive'] and available_archives:
    print("\n" + "=" * 80)
    print("STEP 2: fetch_games_from_archive_url(archive_url)")
    print("=" * 80)
    
    # Use the most recent archive
    latest_archive = available_archives[-1]
    
    print(f"\n Fetching games from latest archive: {latest_archive}")
    print("\nWhat this method does:")
    print("  - Takes a full archive URL as input")
    print("  - Directly fetches games from that specific month")
    print("  - Returns: List of game dictionaries (JSON format)")
    print("  - Use case: When you know exactly which month you want")
    
    archive_games = fetcher.fetch_games_from_archive_url(latest_archive)
    
    print(f"\n Fetched {len(archive_games)} games from archive")
    
    if archive_games:
        first_game = archive_games[0]
        print("\n Examining first game structure:")
        print(f"  - White: {first_game['white']['username']} (Rating: {first_game['white']['rating']})")
        print(f"  - Black: {first_game['black']['username']} (Rating: {first_game['black']['rating']})")
        print(f"  - Time Control: {first_game.get('time_class', 'unknown')}")
        print(f"  - Game URL: {first_game.get('url', 'N/A')}")
        
        # Count games by time control
        time_controls = {}
        for game in archive_games:
            tc = game.get('time_class', 'unknown')
            time_controls[tc] = time_controls.get(tc, 0) + 1
        
        print(f"\n Games by time control in this archive:")
        for tc, count in sorted(time_controls.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {tc}: {count}")

# =============================================================================
# STEP 3: FETCH_ALL_GAMES() - THE POWERFUL NEW METHOD!
# =============================================================================

# Check if CSV already exists
csv_path = OUTPUT_DIR / CSV_FILENAME
csv_exists = csv_path.exists()

if csv_exists and not FORCE_REFETCH:
    print("\n" + "=" * 80)
    print("LOADING EXISTING DATA FROM CSV")
    print("=" * 80)
    
    print(f"\n Found existing CSV: {csv_path}")
    print(f"   File size: {csv_path.stat().st_size / 1024:.1f} KB")
    print(f"   Last modified: {datetime.fromtimestamp(csv_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n Loading from CSV instead of fetching from API...")
    print(f"   (Set FORCE_REFETCH = True to fetch fresh data)")
    
    df_processed = pd.read_csv(csv_path)
    
    print(f"\n Loaded {len(df_processed)} games from CSV")
    
    # Quick summary
    print(f"\n Dataset summary:")
    print(f"  - Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
    print(f"  - Columns: {df_processed.shape[1]}")
    print(f"  - Memory usage: {df_processed.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # Skip fetching
    RUN_CONFIG['fetch_all_games'] = False
    RUN_CONFIG['process_and_save'] = False
    all_games = None  # Mark that we didn't fetch
    
elif RUN_CONFIG['fetch_all_games']:
    print("\n" + "=" * 80)
    print("STEP 3: fetch_all_games(username, limit_months=None)")
    print("=" * 80)
    
    if csv_exists:
        print(f"\n CSV exists but FORCE_REFETCH = True, fetching fresh data...")
    else:
        print(f"\n No existing CSV found, fetching from API...")
    
    print(f"\n This is the MOST POWERFUL method in the class!")
    print("\nWhat this method does:")
    print("  - Automatically fetches the complete archive list")
    print("  - Iterates through ALL archives and downloads every game")
    print("  - Implements smart rate limiting (0.5s between requests)")
    print("  - Optional: limit to N most recent months for faster testing")
    print("  - Returns: Complete list of ALL your chess games!")
    
    print(f"\n  Fetching last {FETCH_LIMIT_MONTHS} months of games...")
    print(f"   (Set FETCH_LIMIT_MONTHS=None to get complete history)")
    
    all_games = fetcher.fetch_all_games(USERNAME, limit_months=FETCH_LIMIT_MONTHS)
    
    print(f"\n Fetched total of {len(all_games)} games")
    
    if all_games:
        # Comprehensive analysis
        dates = [datetime.fromtimestamp(g['end_time']) for g in all_games]
        
        print(f"\n Complete dataset analysis:")
        print(f"  - Date range: {min(dates).date()} to {max(dates).date()}")
        print(f"  - Time span: {(max(dates) - min(dates)).days} days")
        
        # Time control distribution
        time_controls = {}
        for game in all_games:
            tc = game.get('time_class', 'unknown')
            time_controls[tc] = time_controls.get(tc, 0) + 1
        
        print(f"\n Complete time control breakdown:")
        for tc, count in sorted(time_controls.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(all_games)) * 100
            print(f"  - {tc}: {count} ({pct:.1f}%)")
        
        # User color distribution
        user_colors = {'white': 0, 'black': 0}
        for game in all_games:
            if game['white']['username'].lower() == USERNAME.lower():
                user_colors['white'] += 1
            else:
                user_colors['black'] += 1
        
        print(f"\n Color distribution:")
        for color, count in user_colors.items():
            pct = (count / len(all_games)) * 100
            print(f"  - {color}: {count} ({pct:.1f}%)")
else:
    all_games = None

# =============================================================================
# STEP 4: FETCH_GAMES() - Single Month (Legacy Method)
# =============================================================================

if RUN_CONFIG['fetch_single_month']:
    print("\n" + "=" * 80)
    print("STEP 4: fetch_games(username, year, month)")
    print("=" * 80)
    
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    print(f"\n Fetching games for {current_year}-{current_month:02d}...")
    print("\nWhat this method does:")
    print("  - Fetches games for a SPECIFIC month")
    print("  - Calls: GET https://api.chess.com/pub/player/{username}/games/{year}/{month}")
    print("  - Use case: When you want just one specific month")
    print("  - Note: fetch_all_games() is usually better for bulk fetching")
    
    games = fetcher.fetch_games(USERNAME, current_year, current_month)
    
    print(f"\n Fetched {len(games)} games for {current_year}-{current_month:02d}")
    
    if games:
        print(f"\n Available data keys in each game:")
        print(f"  {', '.join(sorted(games[0].keys()))}")

# =============================================================================
# STEP 5: FETCH_MULTIPLE_MONTHS() - Date Range
# =============================================================================

if RUN_CONFIG['fetch_date_range']:
    print("\n" + "=" * 80)
    print("STEP 5: fetch_multiple_months(username, start_date, end_date)")
    print("=" * 80)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # Last 2 months
    
    print(f"\n Fetching games from {start_date.date()} to {end_date.date()}")
    print("\nWhat this method does:")
    print("  - Fetches games across a date range")
    print("  - Iterates month-by-month calling fetch_games()")
    print("  - Implements rate limiting")
    print("  - Use case: Specific time period analysis")
    print("  - Note: fetch_all_games() is simpler for complete history")
    
    games_range = fetcher.fetch_multiple_months(USERNAME, start_date, end_date)
    
    print(f"\n Fetched total of {len(games_range)} games")

# =============================================================================
# STEP 6: GET_CURRENT_ELO()
# =============================================================================

if RUN_CONFIG['get_current_elo']:
    print("\n" + "=" * 80)
    print("STEP 6: get_current_elo(username, time_control)")
    print("=" * 80)
    
    print(f"\n Fetching current Elo ratings for {USERNAME}...")
    print("\nWhat this method does:")
    print("  - Calls Chess.com stats API")
    print("  - Returns current rating for specified time control")
    print("  - Available time controls: bullet, blitz, rapid, daily")
    print("  - Use case: Compare current rating to historical performance")
    
    time_controls_to_check = ['bullet', 'blitz', 'rapid', 'daily']
    current_elos = {}
    
    for tc in time_controls_to_check:
        elo = fetcher.get_current_elo(USERNAME, tc)
        current_elos[tc] = elo
    
    print(f"\n Current Elo ratings for {USERNAME}:")
    for tc, elo in current_elos.items():
        if elo:
            print(f"  - {tc.capitalize()}: {elo}")
        else:
            print(f"  - {tc.capitalize()}: No rating available")

# =============================================================================
# STEP 7: PROCESS_AND_SAVE() - The Main Processing Pipeline
# =============================================================================

if RUN_CONFIG['process_and_save']:
    print("\n" + "=" * 80)
    print("STEP 7: process_and_save(username, games, mode='json')")
    print("=" * 80)
    
    print("\n Processing and saving games to CSV...")
    print("\nWhat this method does:")
    print("  - Parses raw game data into structured records")
    print("  - Extracts: ratings, results, openings, ECO codes, time controls")
    print("  - Calculates game duration with validation")
    print("  - Handles edge cases: negative durations, timezone crossings")
    print("  - Removes duplicates based on timestamp + opponent")
    print("  - Filters out invalid game durations")
    print("  - Returns: Clean pandas DataFrame")
    
    if 'all_games' in locals() and all_games:
        print(f"\nℹ  Processing {len(all_games)} games from fetch_all_games()...")
        df_processed = fetcher.process_and_save(USERNAME, all_games, mode='json')
        
        # Save to CSV
        csv_path = OUTPUT_DIR / CSV_FILENAME
        df_processed.to_csv(csv_path, index=False)
        
        print(f"\n Processing complete!")
        print(f"  - Final valid games: {len(df_processed)}")
        print(f"  - Saved to: {csv_path.absolute()}")
        print(f"  - File size: {csv_path.stat().st_size / 1024:.1f} KB")
        
        print(f"\n DataFrame summary:")
        print(f"  - Columns: {df_processed.shape[1]}")
        print(f"  - Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
        print(f"  - Memory usage: {df_processed.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        # Column overview
        print(f"\n Available columns:")
        for col in df_processed.columns:
            non_null = df_processed[col].notna().sum()
            pct = (non_null / len(df_processed)) * 100
            print(f"  - {col}: {non_null}/{len(df_processed)} ({pct:.1f}% complete)")
        
        # Rating statistics
        print(f"\n Rating statistics:")
        print(f"  - User avg rating: {df_processed['user_rating'].mean():.0f}")
        print(f"  - Opponent avg rating: {df_processed['opponent_rating'].mean():.0f}")
        print(f"  - User rating range: {df_processed['user_rating'].min()}-{df_processed['user_rating'].max()}")
        
        # Result distribution
        print(f"\n Result distribution:")
        result_counts = df_processed['result_label'].value_counts()
        for result, count in result_counts.items():
            pct = count / len(df_processed) * 100
            print(f"  - {result}: {count} ({pct:.1f}%)")
        
        # Time control breakdown
        print(f"\n Time control breakdown:")
        tc_counts = df_processed['time_control'].value_counts()
        for tc, count in tc_counts.items():
            pct = count / len(df_processed) * 100
            print(f"  - {tc}: {count} ({pct:.1f}%)")
        
        # Duration statistics (if available)
        if 'game_duration_seconds' in df_processed.columns:
            valid_durations = df_processed['game_duration_seconds'].notna()
            if valid_durations.any():
                print(f"\n Game duration statistics:")
                print(f"  - Games with valid duration: {valid_durations.sum()}/{len(df_processed)}")
                print(f"  - Avg duration: {df_processed['game_duration_seconds'].mean() / 60:.1f} minutes")
                print(f"  - Median duration: {df_processed['game_duration_seconds'].median() / 60:.1f} minutes")
                print(f"  - Min duration: {df_processed['game_duration_seconds'].min() / 60:.1f} minutes")
                print(f"  - Max duration: {df_processed['game_duration_seconds'].max() / 60:.1f} minutes")
        
        print(f"\n Sample of processed data:")
        sample_cols = ['date', 'opponent', 'user_rating', 'opponent_rating', 'result_label', 'opening']
        print(df_processed[sample_cols].head(10).to_string(index=False))
        
    else:
        print("\n  No games available to process")
        print("Run fetch_all_games() or fetch_multiple_months() first")

# =============================================================================
# STEP 8: GET_VALIDATION_REPORT()
# =============================================================================

if RUN_CONFIG['validation_report']:
    print("\n" + "=" * 80)
    print("STEP 8: get_validation_report()")
    print("=" * 80)
    
    print("\n Retrieving duration validation report...")
    print("\nWhat this provides:")
    print("  - Total number of invalid durations detected")
    print("  - Breakdown by issue type (negative, unreasonably long)")
    print("  - Detailed log of problematic games")
    print("  - Helps identify data quality issues")
    
    report = fetcher.get_validation_report()
    
    print(f"\n Validation report:")
    print(f"  - Total invalid durations: {report['total_invalid']}")
    print(f"  - Negative durations: {report['negative_durations']}")
    print(f"  - Unreasonably long (>24h): {report['unreasonably_long']}")
    
    if report['validation_log']:
        print(f"\n First 5 problematic games:")
        for i, log_entry in enumerate(report['validation_log'][:5], 1):
            print(f"  {i}. Reason: {log_entry['reason']}")
            print(f"     Duration: {log_entry['duration']}s")
            print(f"     Opponent: {log_entry['opponent']}")
            print(f"     URL: {log_entry['game_url']}")
    else:
        print("\n No validation issues found - all game durations are valid!")

# =============================================================================
# STEP 9: LOAD_EXISTING_DATA()
# =============================================================================

if RUN_CONFIG['load_existing']:
    print("\n" + "=" * 80)
    print("STEP 9: Loading from CSV (for future runs)")
    print("=" * 80)
    
    print("\n CSV storage enables fast reloading")
    print("\nBenefits of CSV storage:")
    print("  - Instant loading (no API calls needed)")
    print("  - Persistent across sessions")
    print("  - Can be opened in Excel, pandas, or any tool")
    print("  - Enables offline analysis")
    
    csv_path = OUTPUT_DIR / CSV_FILENAME
    
    if csv_path.exists():
        print(f"\n CSV file exists: {csv_path}")
        print(f"   File size: {csv_path.stat().st_size / 1024:.1f} KB")
        print(f"\n To reload this data in the future, simply run:")
        print(f"   df = pd.read_csv('{csv_path}')")
        print(f"\n   This avoids re-fetching from the API!")
        
        # If we have df_processed from earlier, work with it
        if 'df_processed' in locals():
            print(f"\n Current DataFrame in memory:")
            print(f"  - Shape: {df_processed.shape}")
            print(f"  - Games: {len(df_processed)}")
            
            # Opening analysis
            print(f"\n Top 10 most played openings:")
            opening_counts = df_processed['opening'].value_counts().head(10)
            for opening, count in opening_counts.items():
                pct = count / len(df_processed) * 100
                print(f"  - {opening}: {count} ({pct:.1f}%)")
            
            # Opponent analysis
            print(f"\n Unique opponents:")
            print(f"  - Total unique opponents: {df_processed['opponent'].nunique()}")
            most_common = df_processed['opponent'].value_counts().head(1)
            print(f"  - Most frequent opponent: {most_common.index[0]} ({most_common.values[0]} games)")
            
            # Color performance
            print(f"\n Performance by color:")
            for color in ['white', 'black']:
                color_games = df_processed[df_processed['user_color'] == color]
                if len(color_games) > 0:
                    win_rate = (color_games['result'].sum() / len(color_games)) * 100
                    wins = (color_games['result'] == 1).sum()
                    losses = (color_games['result'] == 0).sum()
                    draws = (color_games['result'] == 0.5).sum()
                    print(f"  - {color.capitalize()}: {win_rate:.1f}% win rate")
                    print(f"    W: {wins} | L: {losses} | D: {draws} | Total: {len(color_games)}")
    else:
        print(f"\n CSV file not found: {csv_path}")
        print("   Run process_and_save first to create it")

# =============================================================================
# SUMMARY AND NEXT STEPS
# =============================================================================

print("\n" + "=" * 80)
print("EXPLORATION COMPLETE!")
print("=" * 80)

print("\n Methods demonstrated:")
methods = [
    "1. get_available_archives() - Discover all available game archives",
    "2. fetch_games_from_archive_url() - Fetch specific archive directly",
    "3. fetch_all_games() - Fetch COMPLETE game history (RECOMMENDED!)",
    "4. fetch_games() - Fetch single month (legacy)",
    "5. fetch_multiple_months() - Fetch date range",
    "6. get_current_elo() - Get current player ratings",
    "7. process_and_save() - Parse, validate, and save games",
    "8. get_validation_report() - View data quality issues",
]
for method in methods:
    print(f"  {method}")

print("\n Key features highlighted:")
features = [
    " Comprehensive game fetching with fetch_all_games()",
    " Smart duration validation (handles timezones, negative durations)",
    " Duplicate detection and removal",
    " Rich game metadata (openings, ECO codes, URLs)",
    " Performance analytics ready (ratings, results, colors)",
    " Data quality monitoring and reporting",
]
for feature in features:
    print(f"  {feature}")

print("\n Blog post angle suggestions:")
print("  1. 'How to Download Your Entire Chess.com History in Python'")
print("  2. 'Building a Chess Analytics Pipeline: From API to Insights'")
print("  3. 'Data Quality Matters: Handling Edge Cases in Chess Game Data'")
print("  4. 'Your Chess Journey in Data: Complete Historical Analysis'")

print("\n Potential analysis topics:")
print("  - Rating progression over time")
print("  - Opening repertoire evolution")
print("  - Performance by time control")
print("  - Win rate vs. rating differential")
print("  - Game duration patterns")
print("  - Color imbalance effects")
print("  - Most challenging opponents")

print("\n Ready for analysis!")
if 'df_processed' in locals():
    print(f"  - Total games processed: {len(df_processed)}")
    print(f"  - Data spans: {df_processed['date'].min()} to {df_processed['date'].max()}")
    print(f"  - Saved to: {OUTPUT_DIR / CSV_FILENAME}")
else:
    print(f"  - No data processed yet")

print("\n" + "=" * 80)