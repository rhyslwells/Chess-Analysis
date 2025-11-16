"""
data_fetcher.py
Handles fetching game data from Chess.com API and storing it locally.
"""

import os
import glob
import requests
import chess.pgn
import io
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

class ChessDataFetcher:
    """Fetches and processes chess game data from Chess.com API."""
    
    BASE_URL = "https://api.chess.com/pub/player"
    HEADERS = {
        "User-Agent": "Chess Analysis Dashboard (Python/requests)"
    }
    
    def __init__(self, data_dir="data"):
        """Initialize fetcher with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.pgn_dir = self.data_dir / "pgns"
        self.pgn_dir.mkdir(exist_ok=True)
        
    def get_archives_list(self, username):
        """
        Get list of all monthly archives available for a user.
        
        Args:
            username: Chess.com username
            
        Returns:
            List of archive URLs
        """
        url = f"{self.BASE_URL}/{username}/games/archives"
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            archives = response.json().get('archives', [])
            return archives
        except requests.exceptions.RequestException as e:
            print(f"Error fetching archives: {e}")
            return []
    
    def fetch_games(self, username, year=None, month=None):
        """
        Fetch games for a username from Chess.com.
        
        Args:
            username: Chess.com username
            year: Year to fetch (if None, fetches current month)
            month: Month to fetch (if None, fetches current month)
            
        Returns:
            List of game dictionaries
        """
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
            
        url = f"{self.BASE_URL}/{username}/games/{year}/{month:02d}"
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('games', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")
            return []
    
    def fetch_pgn_for_month(self, username, year, month):
        """
        Fetch PGN file for a specific month.
        
        Args:
            username: Chess.com username
            year: Year to fetch
            month: Month to fetch
            
        Returns:
            PGN text content
        """
        url = f"{self.BASE_URL}/{username}/games/{year}/{month:02d}/pgn"
        
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching PGN for {year}-{month:02d}: {e}")
            return ""
    
    def download_all_pgns(self, username):
        """
        Download all available PGN files for a user.
        
        Args:
            username: Chess.com username
            
        Returns:
            Number of PGN files downloaded
        """
        archives = self.get_archives_list(username)
        
        if not archives:
            print(f"No archives found for user: {username}")
            return 0
        
        print(f"Found {len(archives)} monthly archives for {username}")
        
        downloaded = 0
        for archive_url in archives:
            # Extract year and month from URL
            parts = archive_url.split('/')
            year = parts[-2]
            month = parts[-1]
            
            pgn_url = f"{archive_url}/pgn"
            pgn_path = self.pgn_dir / f"{username}_{year}_{month}.pgn"
            
            # Skip if already downloaded
            if pgn_path.exists():
                print(f"  Skipping {year}-{month} (already exists)")
                continue
            
            print(f"  Downloading {year}-{month}...")
            
            try:
                response = requests.get(pgn_url, headers=self.HEADERS, timeout=10)
                response.raise_for_status()
                
                with open(pgn_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                downloaded += 1
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"  Failed to download {year}-{month}: {e}")
                continue
        
        print(f"Downloaded {downloaded} new PGN files")
        return downloaded
    
    def merge_pgns(self, username):
        """
        Merge all PGN files for a user into a single file.
        
        Args:
            username: Chess.com username
            
        Returns:
            Path to merged PGN file
        """
        pgn_files = sorted(glob.glob(str(self.pgn_dir / f"{username}_*.pgn")))
        
        if not pgn_files:
            print(f"No PGN files found for {username}")
            return None
        
        merged_path = self.data_dir / f"{username}_all_games.pgn"
        
        with open(merged_path, 'w', encoding='utf-8') as outfile:
            for fpath in pgn_files:
                with open(fpath, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
        
        print(f"Merged {len(pgn_files)} PGN files into {merged_path}")
        return merged_path
    
    def fetch_multiple_months(self, username, start_date, end_date):
        """
        Fetch games across multiple months.
        
        Args:
            username: Chess.com username
            start_date: datetime object for start
            end_date: datetime object for end
            
        Returns:
            List of all games in date range
        """
        all_games = []
        current = start_date
        
        while current <= end_date:
            print(f"Fetching games for {current.year}-{current.month:02d}...")
            games = self.fetch_games(username, current.year, current.month)
            all_games.extend(games)
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
            
            time.sleep(0.5)  # Rate limiting
            
        return all_games
    
    def parse_game_from_json(self, game_data, username):
        """
        Parse a single game from JSON API response into structured format.
        
        Args:
            game_data: Raw game data from API
            username: User's chess.com username
            
        Returns:
            Dictionary with parsed game information
        """
        # Determine user color
        white_player = game_data['white']['username'].lower()
        black_player = game_data['black']['username'].lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'
        
        # Get ratings
        user_rating = game_data[user_color]['rating']
        opponent_rating = game_data[opponent_color]['rating']
        opponent_username = game_data[opponent_color]['username']
        
        # Determine result
        result_str = game_data[user_color].get('result', 'unknown')
        if result_str == 'win':
            result = 1
            result_label = 'Win'
        elif result_str in ['checkmated', 'resigned', 'timeout', 'abandoned']:
            result = 0
            result_label = 'Loss'
        else:
            result = 0.5
            result_label = 'Draw'
        
        # Parse PGN for opening
        pgn_text = game_data.get('pgn', '')
        opening, eco = self._extract_opening_from_pgn(pgn_text)
        
        # Get game URL
        game_url = game_data.get('url', '')
        
        # Parse timestamp
        end_time = datetime.fromtimestamp(game_data['end_time'])
        
        return {
            'date': end_time.strftime('%Y-%m-%d'),
            'timestamp': game_data['end_time'],
            'user_color': user_color,
            'user_rating': user_rating,
            'opponent': opponent_username,
            'opponent_rating': opponent_rating,
            'result': result,
            'result_label': result_label,
            'opening': opening,
            'eco': eco,
            'time_control': game_data.get('time_class', 'unknown'),
            'game_url': game_url,
            'pgn': pgn_text
        }
    
    def parse_game_from_pgn(self, game, username):
        """
        Parse a chess.pgn.Game object into structured format.
        
        Args:
            game: chess.pgn.Game object
            username: User's chess.com username
            
        Returns:
            Dictionary with parsed game information
        """
        headers = game.headers
        
        # Determine user color
        white_player = headers.get('White', '').lower()
        black_player = headers.get('Black', '').lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'
        
        # Get ratings
        user_rating = int(headers.get('WhiteElo' if user_color == 'white' else 'BlackElo', 0))
        opponent_rating = int(headers.get('BlackElo' if user_color == 'white' else 'WhiteElo', 0))
        opponent_username = headers.get('Black' if user_color == 'white' else 'White', 'Unknown')
        
        # Determine result from user perspective
        result_str = headers.get('Result', '*')
        if result_str == '1-0':
            result = 1 if user_color == 'white' else 0
            result_label = 'Win' if user_color == 'white' else 'Loss'
        elif result_str == '0-1':
            result = 0 if user_color == 'white' else 1
            result_label = 'Loss' if user_color == 'white' else 'Win'
        elif result_str == '1/2-1/2':
            result = 0.5
            result_label = 'Draw'
        else:
            result = 0.5
            result_label = 'Unknown'
        
        # Extract moves in SAN notation
        moves = []
        board = game.board()
        node = game
        while node.variations:
            next_node = node.variation(0)
            san = board.san(next_node.move)
            moves.append(san)
            board.push(next_node.move)
            node = next_node
        
        # Parse date
        date_str = headers.get('UTCDate', headers.get('Date', ''))
        try:
            date_obj = datetime.strptime(date_str, '%Y.%m.%d')
            timestamp = int(date_obj.timestamp())
            date_formatted = date_obj.strftime('%Y-%m-%d')
        except:
            timestamp = 0
            date_formatted = date_str
        
        return {
            'date': date_formatted,
            'timestamp': timestamp,
            'user_color': user_color,
            'user_rating': user_rating,
            'opponent': opponent_username,
            'opponent_rating': opponent_rating,
            'result': result,
            'result_label': result_label,
            'opening': headers.get('Opening', 'Unknown'),
            'eco': headers.get('ECO', ''),
            'time_control': headers.get('TimeControl', 'unknown'),
            'game_url': headers.get('Link', ''),
            'termination': headers.get('Termination', ''),
            'moves_san': ' '.join(moves)
        }
    
    def _extract_opening_from_pgn(self, pgn_text):
        """
        Extract opening name and ECO code from PGN text.
        
        Args:
            pgn_text: PGN format game text
            
        Returns:
            Tuple of (opening_name, eco_code)
        """
        try:
            pgn = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)
            if game:
                opening = game.headers.get('Opening', 
                    game.headers.get('ECOUrl', 'Unknown').split('/')[-1].replace('-', ' ').title()
                )
                eco = game.headers.get('ECO', '')
                return opening, eco
            return 'Unknown', ''
        except:
            return 'Unknown', ''
    
    def pgn_to_dataframe(self, pgn_path, username):
        """
        Convert a PGN file to a pandas DataFrame.
        
        Args:
            pgn_path: Path to PGN file
            username: Chess.com username for perspective
            
        Returns:
            DataFrame with parsed games
        """
        records = []
        
        with open(pgn_path, 'r', encoding='utf-8') as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                
                record = self.parse_game_from_pgn(game, username)
                records.append(record)
        
        return pd.DataFrame(records)
    
    def process_and_save(self, username, games, mode='json'):
        """
        Process games and save to CSV.
        
        Args:
            username: Chess.com username
            games: List of raw game data (JSON) or path to PGN file
            mode: 'json' for API data or 'pgn' for PGN file
            
        Returns:
            DataFrame of processed games
        """
        if mode == 'pgn':
            # games should be a path to PGN file
            df = self.pgn_to_dataframe(games, username)
        else:
            # games is a list of JSON game objects
            processed_games = [self.parse_game_from_json(game, username) for game in games]
            df = pd.DataFrame(processed_games)
        
        # Sort by date
        df = df.sort_values('timestamp', ascending=False)
        
        # Remove duplicates based on timestamp and opponent
        df = df.drop_duplicates(subset=['timestamp', 'opponent'], keep='first')
        
        # Save to CSV
        csv_path = self.data_dir / f"{username}_games.csv"
        
        # Merge with existing data if it exists
        if csv_path.exists():
            existing_df = pd.read_csv(csv_path)
            df = pd.concat([df, existing_df], ignore_index=True)
            df = df.drop_duplicates(subset=['timestamp', 'opponent'], keep='first')
            df = df.sort_values('timestamp', ascending=False)
        
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} games to {csv_path}")
        
        return df
    
    def load_existing_data(self, username):
        """Load existing game data from CSV if it exists."""
        csv_path = self.data_dir / f"{username}_games.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return None
    
    def fetch_and_process_all(self, username):
        """
        Comprehensive fetch: download all PGNs, merge, and convert to CSV.
        
        Args:
            username: Chess.com username
            
        Returns:
            DataFrame of all processed games
        """
        print(f"Starting comprehensive fetch for {username}...")
        
        # Download all PGNs
        self.download_all_pgns(username)
        
        # Merge PGNs
        merged_pgn = self.merge_pgns(username)
        
        if merged_pgn is None:
            print("No PGN files to process")
            return None
        
        # Convert to DataFrame and save
        df = self.process_and_save(username, merged_pgn, mode='pgn')
        
        print(f"Comprehensive fetch complete: {len(df)} games processed")
        return df