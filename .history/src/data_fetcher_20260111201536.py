"""
data_fetcher.py
Handles fetching game data from Chess.com API and storing it locally.
"""

import glob
import requests
import chess.pgn
import io
import pandas as pd
from datetime import datetime
import time

import requests
import chess.pgn
import pandas as pd
from datetime import datetime
import io
import time

class ChessDataFetcher:
    """Fetches and processes chess game data from Chess.com API."""

    BASE_URL = "https://api.chess.com/pub/player"
    HEADERS = {
        "User-Agent": "Chess Analysis Dashboard (Python/requests)"
    }

    def __init__(self):
        pass

    # ----------------------------
    # Fetching games from API
    # ----------------------------
    def fetch_games(self, username, year=None, month=None):
        """Fetch games for a username from Chess.com API for a given month."""
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

    def fetch_multiple_months(self, username, start_date, end_date):
        """Fetch games across multiple months."""
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

    # ----------------------------
    # PGN parsing
    # ----------------------------
    def parse_game_from_json(self, game_data, username):
        """
        Parse a single game from JSON API response into structured format.
        Adds ECOUrl and total game time.
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

        # Add ECO URL
        try:
            eco_url = chess.pgn.read_game(io.StringIO(pgn_text)).headers.get(
                'ECOUrl', "https://www.chess.com/openings/Undefined"
            )
        except:
            eco_url = "https://www.chess.com/openings/Undefined"

        # Parse timestamps
        end_time = datetime.fromtimestamp(game_data['end_time'])
        date_str = end_time.strftime('%Y-%m-%d')

        # Compute total time if StartTime exists
        start_time_str = game_data.get('StartTime', None)
        if start_time_str:
            try:
                h, m, s = map(int, start_time_str.split(':'))
                start_seconds = h * 3600 + m * 60 + s
                total_seconds = game_data['end_time'] - start_seconds
            except:
                total_seconds = None
        else:
            total_seconds = None

        return {
            'date': date_str,
            'timestamp': game_data['end_time'],
            'user_color': user_color,
            'user_rating': user_rating,
            'opponent': opponent_username,
            'opponent_rating': opponent_rating,
            'result': result,
            'result_label': result_label,
            'opening': opening,
            'eco': eco,
            'eco_url': eco_url,
            'time_control': game_data.get('time_class', 'unknown'),
            'game_url': game_data.get('url', ''),
            'pgn': pgn_text,
            'total_time_seconds': total_seconds
        }


    def pgn_to_dataframe(self, pgn_path, username):
        """Convert a PGN file to a pandas DataFrame."""
        records = []
        with open(pgn_path, 'r', encoding='utf-8') as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                record = self.parse_game_from_pgn(game, username)
                records.append(record)
        return pd.DataFrame(records)

    # ----------------------------
    # Process and save
    # ----------------------------
    def process_and_save(self, username, games, mode='pgn'):
        """
        Process games and return DataFrame.
        mode='pgn': games is path to PGN file
        """
        if mode == 'pgn':
            df = self.pgn_to_dataframe(games, username)
        else:
            raise NotImplementedError("Only 'pgn' mode is supported in minimal version")

        df = df.sort_values('timestamp', ascending=False)
        df = df.drop_duplicates(subset=['timestamp', 'opponent'], keep='first')
        return df
