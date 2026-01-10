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

# Import required libraries
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Add parent directory to path

import pandas as pd
from datetime import datetime
from src.data_fetcher import ChessDataFetcher

"""
Initialize the Data Fetcher

Create an instance of ChessDataFetcher. By default, it uses a 'data' directory for storing files.
"""

# Initialize the data fetcher
fetcher = ChessDataFetcher()
# print(f"Data directory: {fetcher.data_dir}")
# print(f"PGN directory: {fetcher.pgn_dir}")

"""
Fetch Archives List

Get the list of all monthly archives available for a user. This shows what data is available on Chess.com.
"""

# Example username (replace with your own)
username = "RhysLWells"  # You can change this to any Chess.com username

# Get archives list
archives = fetcher.get_archives_list(username)
print(f"Found {len(archives)} archives for {username}")
print("First 5 archives:")
for archive in archives[:5]:
    print(archive)

"""
Fetch Games for a Specific Month

Fetch games for a specific month using the JSON API.
"""

# Fetch games for a specific month (e.g., current month)
current_year = datetime.now().year
current_month = datetime.now().month

games = fetcher.fetch_games(username, current_year, current_month)
print(f"Fetched {len(games)} games for {current_year}-{current_month:02d}")

# Show details of the first game
if games:
    first_game = games[0]
    print("\nFirst game details:")
    print(f"White: {first_game['white']['username']} ({first_game['white']['rating']})")
    print(f"Black: {first_game['black']['username']} ({first_game['black']['rating']})")
    print(f"Result: {first_game['white']['result']} - {first_game['black']['result']}")
    print(f"Time Control: {first_game.get('time_class', 'unknown')}")
else:
    print("No games found for this month.")

"""
Fetch Games Across Multiple Months

Use fetch_multiple_months to get games for a date range.
"""

# Fetch games for the last 3 months
from datetime import timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

print(f"Fetching games from {start_date.date()} to {end_date.date()}")

games_range = fetcher.fetch_multiple_months(username, start_date, end_date)
print(f"Total games fetched: {len(games_range)}")

"""
Process and Save Games

Convert the fetched games to a pandas DataFrame and save to CSV.
"""

# Process the games into a DataFrame
if games_range:
    df = fetcher.process_and_save(username, games_range, mode='json')
    print(f"Processed {len(df)} games")
    print("\nDataFrame columns:")
    print(df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
else:
    print("No games to process")

"""
Load Existing Data

If you've already saved data, you can load it from CSV.
"""

# Load existing data
existing_df = fetcher.load_existing_data(username)
if existing_df is not None:
    print(f"Loaded {len(existing_df)} existing games")
    print("Data types:")
    print(existing_df.dtypes)
else:
    print("No existing data found")

"""
Download and Process PGN Files

For a more comprehensive approach, download all PGN files and process them.
"""

# Download all PGN files (this may take time for users with many games)
# Uncomment the following lines to run (be mindful of rate limits)

# print("Downloading PGN files...")
# downloaded = fetcher.download_all_pgns(username)
# print(f"Downloaded {downloaded} new PGN files")

# # Merge and process all PGN files
# merged_pgn = fetcher.merge_pgns(username)
# if merged_pgn:
#     df_pgn = fetcher.process_and_save(username, merged_pgn, mode='pgn')
#     print(f"Processed {len(df_pgn)} games from PGN")

"""
Comprehensive Fetch

Use the fetch_and_process_all method for a complete data pipeline.
"""

# Comprehensive fetch (downloads all PGNs, merges, and processes)
# Uncomment to run (this will download all available data)

# df_all = fetcher.fetch_and_process_all(username)
# if df_all is not None:
#     print(f"Total games processed: {len(df_all)}")
#     print("Summary statistics:")
#     print(df_all.describe())

"""
Data Exploration

Once you have the data, you can explore it further.
"""

# Basic exploration (assuming df exists from earlier processing)
if 'df' in locals() and not df.empty:
    print("Basic statistics:")
    print(f"Total games: {len(df)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Average user rating: {df['user_rating'].mean():.0f}")
    print(f"Average opponent rating: {df['opponent_rating'].mean():.0f}")
    
    print("\nWin/Loss/Draw distribution:")
    print(df['result_label'].value_counts())
    
    print("\nGames by time control:")
    print(df['time_control'].value_counts())
else:
    print("No data to explore. Run the processing steps above first.")

"""
Tips and Best Practices

1. Rate Limiting: Chess.com API has rate limits. The code includes time.sleep(0.5) to be respectful.
2. Data Storage: Data is stored in the data/ directory. PGNs go in data/pgns/.
3. Incremental Updates: The process_and_save method merges new data with existing CSV files.
4. Error Handling: Methods include try-except blocks for network errors.
5. Large Datasets: For users with thousands of games, consider processing in batches.

Next Steps:
- Integrate with the analyzer and predictor modules
- Create visualizations of your chess performance
- Build machine learning models for game prediction

This script provides a foundation for exploring chess data. Modify the username and parameters as needed for your analysis.
"""
