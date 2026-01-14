"""
data_fetcher.py
Handles fetching game data from Chess.com API and storing it locally.
"""

import requests
import chess.pgn
import io
import pandas as pd
from datetime import datetime
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

    def get_current_elo(self, username: str, time_control: str = "blitz") -> int | None:
        """
        Fetch current Elo for a given username and time control.
        Returns None if not available.
        """
        url = f"https://api.chess.com/pub/player/{username}/stats"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            stats = response.json()

            control_map = {
                "bullet": "chess_bullet",
                "blitz": "chess_blitz",
                "rapid": "chess_rapid",
                "daily": "chess_daily"
            }

            key = control_map.get(time_control.strip().lower())
            if not key:
                return None

            # Debug: ensure key exists
            if key not in stats:
                print(f"No stats for {time_control} ({key})")
                return None

            last_rating_info = stats[key].get("last")
            if not last_rating_info:
                print(f"No last rating info for {time_control}")
                return None

            rating = last_rating_info.get("rating")
            return rating

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Elo for {username}: {e}")
            return None


    # ----------------------------
    # PGN parsing
    # ----------------------------

    def parse_game_from_json(self, game_data, username):
        """
        Parse a single game from JSON API response into structured format.
        """

        # --- Determine user color ---
        white_player = game_data['white']['username'].lower()
        black_player = game_data['black']['username'].lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'

        # --- Ratings ---
        user_rating = game_data[user_color]['rating']
        opponent_rating = game_data[opponent_color]['rating']
        opponent_username = game_data[opponent_color]['username']

        # --- Result ---
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

        # --- PGN parsing ---
        pgn_text = game_data.get('pgn', '')
        opening = 'Unknown'
        eco = ''
        eco_url = 'https://www.chess.com/openings/Undefined'
        game_duration_seconds = None

        try:
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if game:
                headers = game.headers

                eco = headers.get('ECO', '')
                eco_url = headers.get(
                    'ECOUrl',
                    'https://www.chess.com/openings/Undefined'
                )

                # Opening resolution logic (DO NOT overwrite blindly)
                if 'Opening' in headers and headers['Opening'].strip():
                    opening = headers['Opening']
                elif eco_url:
                    opening = (
                        eco_url
                        .rstrip('/')
                        .split('/')[-1]
                        .replace('-', ' ')
                        .title()
                    )

                # --- Time calculation ---
                start_time_str = headers.get('StartTime')   # HH:MM:SS
                end_date_str = headers.get('EndDate')       # YYYY.MM.DD
                end_time_str = headers.get('EndTime')       # HH:MM:SS (optional)

                if start_time_str and end_date_str:
                    start_dt = datetime.strptime(
                        f"{end_date_str} {start_time_str}",
                        "%Y.%m.%d %H:%M:%S"
                    )

                    if end_time_str:
                        end_dt = datetime.strptime(
                            f"{end_date_str} {end_time_str}",
                            "%Y.%m.%d %H:%M:%S"
                        )
                    else:
                        end_dt = datetime.fromtimestamp(game_data['end_time'])

                    game_duration_seconds = int(
                        (end_dt - start_dt).total_seconds()
                    )

        except Exception as e:
            print(f"PGN parsing error: {e}")


        # --- Timestamp ---
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
            'eco_url': eco_url,
            'time_control': game_data.get('time_class', 'unknown'),
            'game_url': game_data.get('url', ''),
            'game_duration_seconds': game_duration_seconds,
            'pgn': pgn_text,
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
        return df