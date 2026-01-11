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
    def parse_game_from_pgn(self, game, username):
        """Parse a chess.pgn.Game object into structured format."""
        headers = game.headers

        white_player = headers.get('White', '').lower()
        black_player = headers.get('Black', '').lower()
        user_color = 'white' if white_player == username.lower() else 'black'
        opponent_color = 'black' if user_color == 'white' else 'white'

        user_rating = int(headers.get('WhiteElo' if user_color == 'white' else 'BlackElo', 0))
        opponent_rating = int(headers.get('BlackElo' if user_color == 'white' else 'WhiteElo', 0))
        opponent_username = headers.get('Black' if user_color == 'white' else 'White', 'Unknown')

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

        moves = []
        board = game.board()
        node = game
        while node.variations:
            next_node = node.variation(0)
            san = board.san(next_node.move)
            moves.append(san)
            board.push(next_node.move)
            node = next_node

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
