"""
Chess Data Fetcher Exploration Script

This script demonstrates how to use the ChessDataFetcher class from src/data_fetcher.py
to fetch and process chess game data from Chess.com. It can be run in IPython or as a regular Python script.

Overview:
The ChessDataFetcher class provides methods to:
- Fetch game archives for a user
- Download PGN files
- Parse games from JSON API responses or PGN files
- Convert data to pandas DataFrames
- Save processed data to CSV

Setup:
First, let's import the necessary libraries and the ChessDataFetcher class.
"""

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
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Add parent directory to path


import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
from src.data_fetcher import ChessDataFetcher

# Import our data fetcher

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set your Chess.com username here
USERNAME = "RhysLWells"

# Control which sections to run (useful for testing specific features)
RUN_CONFIG = {
    'get_archives': True,        # Step 1: Get list of available archives
    'fetch_single_month': True,  # Step 2: Fetch games for one month
    'fetch_date_range': True,    # Step 3: Fetch games for date range
    'fetch_pgn_month': True,     # Step 4: Fetch PGN for specific month
    'download_all_pgns': False,  # Step 5: Download ALL PGNs (can be slow!)
    'merge_pgns': False,         # Step 6: Merge PGN files
    'pgn_to_dataframe': False,   # Step 7: Convert PGN to DataFrame
    'process_and_save': True,    # Step 8: Process and save to CSV
    'load_existing': True,       # Step 9: Load existing CSV
    'comprehensive_fetch': False # Step 10: All-in-one fetch (slow!)
}

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

print("\n📦 Creating ChessDataFetcher instance...")
print("\nWhat happens during initialization:")
print("  1. Sets base URL for Chess.com API")
print("  2. Configures User-Agent header (required for API etiquette)")
print("  3. Creates 'data/' directory if it doesn't exist")
print("  4. Creates 'data/pgns/' subdirectory for PGN files")

fetcher = ChessDataFetcher()

print(f"\n✅ Fetcher initialized successfully!")
print(f"  - Data directory: {fetcher.data_dir}")
print(f"  - PGN directory: {fetcher.pgn_dir}")
print(f"  - Base URL: {fetcher.BASE_URL}")
print(f"  - User-Agent: {fetcher.HEADERS['User-Agent']}")

# =============================================================================
# STEP 1: GET_ARCHIVES_LIST()
# =============================================================================

if RUN_CONFIG['get_archives']:
    print("\n" + "=" * 80)
    print("STEP 1: get_archives_list(username)")
    print("=" * 80)
    
    print(f"\n📋 Fetching list of available archives for {USERNAME}...")
    print("\nWhat this method does:")
    print("  - Calls: GET https://api.chess.com/pub/player/{username}/games/archives")
    print("  - Returns: List of URLs pointing to monthly game archives")
    print("  - Purpose: Discover what data is available before downloading")
    
    archives = fetcher.get_archives_list(USERNAME)
    
    print(f"\n✅ Found {len(archives)} monthly archives")
    
    if archives:
        print("\n📅 First 5 archives:")
        for i, archive in enumerate(archives[:5], 1):
            # Extract year/month from URL
            parts = archive.split('/')
            year, month = parts[-2], parts[-1]
            print(f"  {i}. {year}-{month}: {archive}")
        
        print(f"\n📅 Last 5 archives:")
        for i, archive in enumerate(archives[-5:], len(archives)-4):
            parts = archive.split('/')
            year, month = parts[-2], parts[-1]
            print(f"  {i}. {year}-{month}: {archive}")
        
        # Parse dates from archives
        first_archive = archives[0].split('/')
        last_archive = archives[-1].split('/')
        print(f"\n📊 Archive summary:")
        print(f"  - Earliest: {first_archive[-2]}-{first_archive[-1]}")
        print(f"  - Latest: {last_archive[-2]}-{last_archive[-1]}")
        print(f"  - Total months: {len(archives)}")
    else:
        print("❌ No archives found (check username)")

# =============================================================================
# STEP 2: FETCH_GAMES() - Single Month
# =============================================================================

if RUN_CONFIG['fetch_single_month']:
    print("\n" + "=" * 80)
    print("STEP 2: fetch_games(username, year, month)")
    print("=" * 80)
    
    # Get current month
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    print(f"\n🎮 Fetching games for {current_year}-{current_month:02d}...")
    print("\nWhat this method does:")
    print("  - Calls: GET https://api.chess.com/pub/player/{username}/games/{year}/{month}")
    print("  - Returns: List of game dictionaries (JSON format)")
    print("  - Contains: Full game data including PGN, ratings, results, URLs")
    
    games = fetcher.fetch_games(USERNAME, current_year, current_month)
    
    print(f"\n✅ Fetched {len(games)} games for {current_year}-{current_month:02d}")
    
    if games:
        first_game = games[0]
        print("\n🔍 Examining first game structure:")
        print(f"  - White: {first_game['white']['username']} (Rating: {first_game['white']['rating']})")
        print(f"  - Black: {first_game['black']['username']} (Rating: {first_game['black']['rating']})")
        print(f"  - Result: {first_game.get('white', {}).get('result', 'N/A')} vs {first_game.get('black', {}).get('result', 'N/A')}")
        print(f"  - Time Control: {first_game.get('time_class', 'unknown')}")
        print(f"  - Game URL: {first_game.get('url', 'N/A')}")
        print(f"  - End Time: {datetime.fromtimestamp(first_game['end_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📊 Available data keys in each game:")
        print(f"  {', '.join(sorted(first_game.keys()))}")
        
        # Count games by time control
        time_controls = {}
        for game in games:
            tc = game.get('time_class', 'unknown')
            time_controls[tc] = time_controls.get(tc, 0) + 1
        
        print(f"\n📊 Games by time control:")
        for tc, count in sorted(time_controls.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {tc}: {count}")
    else:
        print("ℹ️ No games found for this month")

# =============================================================================
# STEP 3: FETCH_MULTIPLE_MONTHS() - Date Range
# =============================================================================

if RUN_CONFIG['fetch_date_range']:
    print("\n" + "=" * 80)
    print("STEP 3: fetch_multiple_months(username, start_date, end_date)")
    print("=" * 80)
    
    # Define date range (last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"\n📅 Fetching games from {start_date.date()} to {end_date.date()}")
    print("\nWhat this method does:")
    print("  - Iterates through each month in the date range")
    print("  - Calls fetch_games() for each month")
    print("  - Implements rate limiting (0.5s delay between requests)")
    print("  - Returns: Combined list of all games in range")
    
    print(f"\nℹ️ This will make ~{((end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1)} API requests")
    
    games_range = fetcher.fetch_multiple_months(USERNAME, start_date, end_date)
    
    print(f"\n✅ Fetched total of {len(games_range)} games")
    
    if games_range:
        # Analyze date distribution
        dates = [datetime.fromtimestamp(g['end_time']).date() for g in games_range]
        print(f"\n📊 Date range of fetched games:")
        print(f"  - Earliest: {min(dates)}")
        print(f"  - Latest: {max(dates)}")
        print(f"  - Span: {(max(dates) - min(dates)).days} days")

# =============================================================================
# STEP 4: FETCH_PGN_FOR_MONTH() - Get PGN Text
# =============================================================================

if RUN_CONFIG['fetch_pgn_month']:
    print("\n" + "=" * 80)
    print("STEP 4: fetch_pgn_for_month(username, year, month)")
    print("=" * 80)
    
    # Use current month
    pgn_year = datetime.now().year
    pgn_month = datetime.now().month
    
    print(f"\n📄 Fetching PGN text for {pgn_year}-{pgn_month:02d}...")
    print("\nWhat this method does:")
    print("  - Calls: GET https://api.chess.com/pub/player/{username}/games/{year}/{month}/pgn")
    print("  - Returns: Raw PGN text (all games for that month)")
    print("  - PGN format: Portable Game Notation (standard chess notation)")
    
    pgn_text = fetcher.fetch_pgn_for_month(USERNAME, pgn_year, pgn_month)
    
    if pgn_text:
        print(f"\n✅ Fetched PGN text ({len(pgn_text)} characters)")
        print("\n📝 First 500 characters of PGN:")
        print("-" * 80)
        print(pgn_text[:500])
        print("-" * 80)
        
        # Count games in PGN (each game starts with [Event)
        game_count = pgn_text.count('[Event ')
        print(f"\n📊 Estimated games in PGN: {game_count}")
    else:
        print("❌ No PGN data retrieved")

# =============================================================================
# STEP 5: DOWNLOAD_ALL_PGNS() - Bulk Download
# =============================================================================

if RUN_CONFIG['download_all_pgns']:
    print("\n" + "=" * 80)
    print("STEP 5: download_all_pgns(username)")
    print("=" * 80)
    
    print(f"\n⚠️ WARNING: This will download ALL available PGN files for {USERNAME}")
    print("This could take several minutes depending on game history!")
    print("\nWhat this method does:")
    print("  - Calls get_archives_list() to find all months")
    print("  - Downloads PGN for each month to data/pgns/")
    print("  - Skips already-downloaded files (incremental)")
    print("  - Implements rate limiting (0.5s between requests)")
    print("  - Saves as: {username}_{year}_{month}.pgn")
    
    input("\nPress Enter to continue or Ctrl+C to skip...")
    
    downloaded_count = fetcher.download_all_pgns(USERNAME)
    
    print(f"\n✅ Download complete!")
    print(f"  - New files downloaded: {downloaded_count}")
    print(f"  - PGN directory: {fetcher.pgn_dir}")
    
    # List downloaded files
    pgn_files = list(fetcher.pgn_dir.glob(f"{USERNAME}_*.pgn"))
    print(f"  - Total PGN files for {USERNAME}: {len(pgn_files)}")

# =============================================================================
# STEP 6: MERGE_PGNS() - Combine PGN Files
# =============================================================================

if RUN_CONFIG['merge_pgns']:
    print("\n" + "=" * 80)
    print("STEP 6: merge_pgns(username)")
    print("=" * 80)
    
    print(f"\n🔗 Merging all PGN files for {USERNAME}...")
    print("\nWhat this method does:")
    print("  - Finds all PGN files matching {username}_*.pgn")
    print("  - Concatenates them into single file")
    print("  - Saves as: data/{username}_all_games.pgn")
    print("  - Adds double newlines between games for separation")
    
    merged_path = fetcher.merge_pgns(USERNAME)
    
    if merged_path:
        print(f"\n✅ PGNs merged successfully!")
        print(f"  - Output file: {merged_path}")
        print(f"  - File size: {merged_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Count games in merged file
        with open(merged_path, 'r', encoding='utf-8') as f:
            content = f.read()
            game_count = content.count('[Event ')
        print(f"  - Total games: {game_count}")
    else:
        print("❌ No PGN files found to merge")

# =============================================================================
# STEP 7: PGN_TO_DATAFRAME() - Parse PGN File
# =============================================================================

if RUN_CONFIG['pgn_to_dataframe']:
    print("\n" + "=" * 80)
    print("STEP 7: pgn_to_dataframe(pgn_path, username)")
    print("=" * 80)
    
    # Check if merged PGN exists
    merged_pgn_path = fetcher.data_dir / f"{USERNAME}_all_games.pgn"
    
    if merged_pgn_path.exists():
        print(f"\n📊 Converting PGN to DataFrame...")
        print("\nWhat this method does:")
        print("  - Reads PGN file game-by-game using python-chess")
        print("  - Calls parse_game_from_pgn() for each game")
        print("  - Extracts: ratings, results, openings, ECO codes, moves")
        print("  - Returns: Pandas DataFrame with structured data")
        
        print(f"\nℹ️ Processing {merged_pgn_path}...")
        df_pgn = fetcher.pgn_to_dataframe(merged_pgn_path, USERNAME)
        
        print(f"\n✅ Converted {len(df_pgn)} games to DataFrame")
        print(f"\n📊 DataFrame info:")
        print(f"  - Shape: {df_pgn.shape}")
        print(f"  - Columns: {', '.join(df_pgn.columns)}")
        print(f"\n📋 First 3 games:")
        print(df_pgn[['date', 'user_rating', 'opponent_rating', 'result_label', 'opening']].head(3).to_string())
    else:
        print(f"\n❌ Merged PGN not found: {merged_pgn_path}")
        print("Run merge_pgns() first or set RUN_CONFIG['merge_pgns'] = True")

# =============================================================================
# STEP 8: PROCESS_AND_SAVE() - Main Processing Pipeline
# =============================================================================

if RUN_CONFIG['process_and_save']:
    print("\n" + "=" * 80)
    print("STEP 8: process_and_save(username, games, mode)")
    print("=" * 80)
    
    print("\n💾 Processing and saving games to CSV...")
    print("\nWhat this method does:")
    print("  - MODE 'json': Parses list of game dictionaries from API")
    print("  - MODE 'pgn': Converts PGN file to DataFrame")
    print("  - Removes duplicate games (by timestamp + opponent)")
    print("  - Merges with existing CSV if present")
    print("  - Saves to: data/{username}_games.csv")
    
    # Use games from Step 3 if available
    if 'games_range' in locals() and games_range:
        print(f"\nℹ️ Processing {len(games_range)} games from API (JSON mode)...")
        df_processed = fetcher.process_and_save(USERNAME, games_range, mode='json')
        
        print(f"\n✅ Processing complete!")
        print(f"  - Games in DataFrame: {len(df_processed)}")
        print(f"  - Saved to: {fetcher.data_dir / f'{USERNAME}_games.csv'}")
        
        print(f"\n📊 DataFrame summary:")
        print(f"  - Columns: {df_processed.shape[1]}")
        print(f"  - Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
        print(f"  - Avg user rating: {df_processed['user_rating'].mean():.0f}")
        print(f"  - Avg opponent rating: {df_processed['opponent_rating'].mean():.0f}")
        
        print(f"\n📋 Sample of processed data:")
        print(df_processed[['date', 'opponent', 'user_rating', 'opponent_rating', 
                            'result_label', 'opening']].head(5).to_string(index=False))
        
        # Result distribution
        print(f"\n📊 Result distribution:")
        result_counts = df_processed['result_label'].value_counts()
        for result, count in result_counts.items():
            pct = count / len(df_processed) * 100
            print(f"  - {result}: {count} ({pct:.1f}%)")
    else:
        print("\n⚠️ No games available to process")
        print("Run fetch_multiple_months or fetch_games first")

# =============================================================================
# STEP 9: LOAD_EXISTING_DATA() - Load from CSV
# =============================================================================

if RUN_CONFIG['load_existing']:
    print("\n" + "=" * 80)
    print("STEP 9: load_existing_data(username)")
    print("=" * 80)
    
    print(f"\n📂 Loading existing CSV for {USERNAME}...")
    print("\nWhat this method does:")
    print("  - Checks if CSV exists: data/{username}_games.csv")
    print("  - Loads using pandas.read_csv()")
    print("  - Returns DataFrame or None if file doesn't exist")
    print("  - Purpose: Quick reload without re-fetching from API")
    
    df_existing = fetcher.load_existing_data(USERNAME)
    
    if df_existing is not None:
        print(f"\n✅ Loaded {len(df_existing)} games from CSV")
        
        print(f"\n📊 Dataset info:")
        print(f"  - Shape: {df_existing.shape}")
        print(f"  - Memory usage: {df_existing.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        print(f"\n📋 Column data types:")
        for col, dtype in df_existing.dtypes.items():
            print(f"  - {col}: {dtype}")
        
        print(f"\n📊 Basic statistics:")
        print(df_existing[['user_rating', 'opponent_rating', 'result']].describe())
        
        # Check for optional columns
        optional_cols = ['eco', 'moves_san', 'termination']
        present = [col for col in optional_cols if col in df_existing.columns]
        missing = [col for col in optional_cols if col not in df_existing.columns]
        
        print(f"\n📊 Optional columns:")
        if present:
            print(f"  ✅ Present: {', '.join(present)}")
        if missing:
            print(f"  ❌ Missing: {', '.join(missing)}")
            print(f"     (Fetch using PGN mode to get these)")
    else:
        print(f"\n❌ No existing CSV found for {USERNAME}")
        print("Process some games first using process_and_save()")

# =============================================================================
# STEP 10: FETCH_AND_PROCESS_ALL() - Complete Pipeline
# =============================================================================

if RUN_CONFIG['comprehensive_fetch']:
    print("\n" + "=" * 80)
    print("STEP 10: fetch_and_process_all(username)")
    print("=" * 80)
    
    print(f"\n🚀 Running comprehensive fetch for {USERNAME}...")
    print("\n⚠️ WARNING: This is the most comprehensive but slowest method!")
    print("\nWhat this method does:")
    print("  1. Calls download_all_pgns() - downloads ALL PGN files")
    print("  2. Calls merge_pgns() - combines into single PGN")
    print("  3. Calls process_and_save(mode='pgn') - converts to CSV")
    print("  4. Returns complete DataFrame with all games")
    print("\nThis can take 5-10 minutes for users with 1000+ games")
    
    input("\nPress Enter to continue or Ctrl+C to skip...")
    
    df_all = fetcher.fetch_and_process_all(USERNAME)
    
    if df_all is not None:
        print(f"\n✅ Comprehensive fetch complete!")
        print(f"  - Total games: {len(df_all)}")
        print(f"  - CSV saved: {fetcher.data_dir / f'{USERNAME}_games.csv'}")
        
        print(f"\n📊 Complete dataset summary:")
        print(f"  - Date range: {df_all['date'].min()} to {df_all['date'].max()}")
        print(f"  - Years of data: {(pd.to_datetime(df_all['date'].max()) - pd.to_datetime(df_all['date'].min())).days / 365:.1f}")
        print(f"  - Unique opponents: {df_all['opponent'].nunique()}")
        
        # Time control breakdown
        print(f"\n📊 Games by time control:")
        tc_counts = df_all['time_control'].value_counts()
        for tc, count in tc_counts.items():
            pct = count / len(df_all) * 100
            print(f"  - {tc}: {count} ({pct:.1f}%)")
        
        # Opening diversity
        print(f"\n📊 Opening diversity:")
        print(f"  - Unique openings: {df_all['opening'].nunique()}")
        print(f"  - Most common: {df_all['opening'].mode()[0]}")
    else:
        print("\n❌ Comprehensive fetch failed")

# =============================================================================
# HELPER METHODS DEMONSTRATION
# =============================================================================

print("\n" + "=" * 80)
print("HELPER METHODS OVERVIEW")
print("=" * 80)

print("\n🔧 Internal helper methods (you typically don't call these directly):")
print("\n1. parse_game_from_json(game_data, username)")
print("   - Converts single API game dict to structured record")
print("   - Determines user color, ratings, result, opening")
print("   - Called internally by process_and_save(mode='json')")

print("\n2. parse_game_from_pgn(game, username)")
print("   - Converts chess.pgn.Game object to structured record")
print("   - Extracts SAN moves, headers, result from user perspective")
print("   - Called internally by pgn_to_dataframe()")

print("\n3. _extract_opening_from_pgn(pgn_text)")
print("   - Private helper to extract opening name and ECO code")
print("   - Returns tuple: (opening_name, eco_code)")
print("   - Handles various PGN header formats")

# =============================================================================
# BEST PRACTICES AND TIPS
# =============================================================================

print("\n" + "=" * 80)
print("BEST PRACTICES AND RECOMMENDATIONS")
print("=" * 80)

print("\n📚 Recommended workflow for new users:")
print("  1. Start with fetch_games() or fetch_multiple_months() for recent games")
print("  2. Use process_and_save(mode='json') to create initial CSV")
print("  3. Use load_existing_data() for subsequent analysis")
print("  4. Periodically fetch new games and merge with existing CSV")

print("\n📚 For complete historical analysis:")
print("  1. Use fetch_and_process_all() once to get everything")
print("  2. This downloads PGNs which include move data")
print("  3. Load from CSV afterwards for speed")

print("\n⚡ Performance tips:")
print("  - API mode (JSON) is faster for recent games")
print("  - PGN mode includes move sequences and termination info")
print("  - CSV loading is instant vs. API fetching (seconds)")
print("  - Rate limiting prevents API blocks (0.5s between requests)")

print("\n🔒 Data privacy:")
print("  - All data is public (Chess.com Published Data API)")
print("  - No authentication required")
print("  - Respect rate limits to avoid IP bans")
print("  - Files stored locally in data/ directory")

print("\n📊 Data quality notes:")
print("  - Duplicate detection by timestamp + opponent")
print("  - Automatic merging with existing data")
print("  - Missing data handled gracefully (defaults to 'Unknown')")
print("  - PGN parsing errors caught and logged")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("EXPLORATION COMPLETE!")
print("=" * 80)

print("\n✅ Methods demonstrated:")
methods = [
    "get_archives_list()",
    "fetch_games()",
    "fetch_multiple_months()",
    "fetch_pgn_for_month()",
    "download_all_pgns()",
    "merge_pgns()",
    "pgn_to_dataframe()",
    "process_and_save()",
    "load_existing_data()",
    "fetch_and_process_all()"
]
for i, method in enumerate(methods, 1):
    print(f"  {i:2d}. {method}")

print(f"\n📁 Generated files (in {fetcher.data_dir}):")
print(f"  - {USERNAME}_games.csv (main dataset)")
if (fetcher.data_dir / f"{USERNAME}_all_games.pgn").exists():
    print(f"  - {USERNAME}_all_games.pgn (merged PGN)")
pgn_files = list(fetcher.pgn_dir.glob(f"{USERNAME}_*.pgn"))
if pgn_files:
    print(f"  - {len(pgn_files)} individual PGN files in pgns/")

print("\n🎯 Next steps:")
print("  1. Review the generated CSV file")
print("  2. Run explore_analyzer.py to analyze the data")
print("  3. Build visualizations and insights")
print("  4. Train ML models for game prediction")

print("\n" + "=" * 80)