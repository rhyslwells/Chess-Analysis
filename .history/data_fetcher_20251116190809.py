"""
data_fetcher.py
Handles fetching game data from Chess.com API and storing it locally.
"""

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
    
    def __init__(self, data_dir="data"):
        """Initialize fetcher with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
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
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('games', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")
            return []
    
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
    
    def parse_game(self, game_data, username):
        """
        Parse a single game into structured format.
        
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
        opening = self._extract_opening(pgn_text)
        
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
            'time_control': game_data.get('time_class', 'unknown'),
            'game_url': game_url,
            'pgn': pgn_text
        }
    
    def _extract_opening(self, pgn_text):
        """Extract opening name from PGN."""
        try:
            pgn = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)
            if game:
                return game.headers.get('ECOUrl', 'Unknown').split('/')[-1].replace('-', ' ').title()
            return 'Unknown'
        except:
            return 'Unknown'
    
    def process_and_save(self, username, games):
        """
        Process games and save to CSV.
        
        Args:
            username: Chess.com username
            games: List of raw game data
            
        Returns:
            DataFrame of processed games
        """
        processed_games = [self.parse_game(game, username) for game in games]
        df = pd.DataFrame(processed_games)
        
        # Sort by date
        df = df.sort_values('timestamp', ascending=False)
        
        # Save to CSV
        csv_path = self.data_dir / f"{username}_games.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} games to {csv_path}")
        
        return df
    
    def load_existing_data(self, username):
        """Load existing game data from CSV if it exists."""
        csv_path = self.data_dir / f"{username}_games.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return None